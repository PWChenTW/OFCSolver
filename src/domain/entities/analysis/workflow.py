"""
Analysis Workflow - Domain Aggregate Root for TASK-014
Based on Architect and Data Specialist recommendations
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field

from ...base import AggregateRoot, DomainEvent
from ...value_objects.expected_value import ExpectedValue


class WorkflowStatus(Enum):
    """Workflow execution status - simplified for MVP"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowStepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Individual step in analysis workflow"""
    step_id: str
    step_type: str  # "validate", "calculate", "aggregate"
    status: WorkflowStepStatus = WorkflowStepStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    
    def start(self) -> None:
        """Start step execution"""
        self.status = WorkflowStepStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete(self, result: Dict[str, Any]) -> None:
        """Mark step as completed"""
        self.status = WorkflowStepStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
    
    def fail(self, error_message: str) -> None:
        """Mark step as failed"""
        self.status = WorkflowStepStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def can_retry(self, max_retries: int = 3) -> bool:
        """Check if step can be retried"""
        return self.status == WorkflowStepStatus.FAILED and self.retry_count < max_retries
    
    def retry(self) -> None:
        """Prepare step for retry"""
        self.retry_count += 1
        self.status = WorkflowStepStatus.PENDING
        self.error_message = None


# Domain Events
@dataclass
class WorkflowStartedEvent(DomainEvent):
    workflow_id: UUID
    steps_count: int
    estimated_duration_seconds: int


@dataclass
class WorkflowCompletedEvent(DomainEvent):
    workflow_id: UUID
    final_result: Dict[str, Any]
    execution_time_ms: int


@dataclass
class WorkflowFailedEvent(DomainEvent):
    workflow_id: UUID
    error_message: str
    failed_step: str


@dataclass
class WorkflowStepCompletedEvent(DomainEvent):
    workflow_id: UUID
    step_id: str
    step_result: Dict[str, Any]


class AnalysisWorkflow(AggregateRoot):
    """
    Analysis Workflow Aggregate Root
    
    Manages the complete lifecycle of analysis orchestration,
    from request to final result aggregation.
    """
    
    def __init__(
        self,
        workflow_id: UUID,
        name: str,
        analysis_request: Dict[str, Any],
        priority: int = 1
    ):
        super().__init__(workflow_id)
        self.workflow_id = workflow_id
        self.name = name
        self.analysis_request = analysis_request
        self.priority = priority
        
        # Workflow state
        self.status = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.estimated_duration_seconds: Optional[int] = None
        
        # Results and metadata
        self.final_result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
        
        # Initialize steps based on analysis request
        self._initialize_steps()
    
    @classmethod
    def create(
        cls,
        name: str,
        analysis_request: Dict[str, Any],
        priority: int = 1
    ) -> 'AnalysisWorkflow':
        """Factory method to create new workflow"""
        workflow_id = uuid4()
        return cls(workflow_id, name, analysis_request, priority)
    
    def _initialize_steps(self) -> None:
        """Initialize workflow steps based on analysis request - MVP version"""
        calculation_mode = self.analysis_request.get('calculation_mode', 'standard')
        
        # MVP: Simple linear workflow
        self.steps = [
            WorkflowStep("validate", "validate_position"),
            WorkflowStep("calculate", f"calculate_{calculation_mode}"),
            WorkflowStep("aggregate", "aggregate_results")
        ]
        
        # Estimate duration based on complexity
        self.estimated_duration_seconds = self._estimate_duration()
    
    def _estimate_duration(self) -> int:
        """Estimate workflow duration based on request complexity"""
        calculation_mode = self.analysis_request.get('calculation_mode', 'standard')
        
        base_times = {
            'instant': 2,
            'standard': 10,
            'exhaustive': 60
        }
        
        base_time = base_times.get(calculation_mode, 10)
        
        # Adjust for position complexity (simplified)
        remaining_cards = len(self.analysis_request.get('remaining_cards', []))
        if remaining_cards > 30:
            base_time *= 1.5
        elif remaining_cards < 10:
            base_time *= 0.7
        
        return int(base_time)
    
    def start(self) -> None:
        """Start workflow execution"""
        if self.status != WorkflowStatus.PENDING:
            raise ValueError(f"Cannot start workflow in status: {self.status}")
        
        self.status = WorkflowStatus.RUNNING
        self.started_at = datetime.utcnow()
        
        # Emit domain event
        self.add_event(WorkflowStartedEvent(
            workflow_id=self.workflow_id,
            steps_count=len(self.steps),
            estimated_duration_seconds=self.estimated_duration_seconds or 0
        ))
    
    def get_current_step(self) -> Optional[WorkflowStep]:
        """Get the current step to execute"""
        for step in self.steps:
            if step.status in [WorkflowStepStatus.PENDING, WorkflowStepStatus.RUNNING]:
                return step
        return None
    
    def complete_step(self, step_id: str, result: Dict[str, Any]) -> None:
        """Mark a step as completed"""
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"Step not found: {step_id}")
        
        step.complete(result)
        
        # Emit step completion event
        self.add_event(WorkflowStepCompletedEvent(
            workflow_id=self.workflow_id,
            step_id=step_id,
            step_result=result
        ))
        
        # Check if workflow is complete
        self._check_workflow_completion()
    
    def fail_step(self, step_id: str, error_message: str) -> None:
        """Mark a step as failed"""
        step = self._find_step(step_id)
        if not step:
            raise ValueError(f"Step not found: {step_id}")
        
        step.fail(error_message)
        
        # Check if step can be retried
        if not step.can_retry():
            self._fail_workflow(f"Step {step_id} failed: {error_message}")
    
    def retry_failed_step(self, step_id: str) -> bool:
        """Retry a failed step"""
        step = self._find_step(step_id)
        if not step or not step.can_retry():
            return False
        
        step.retry()
        return True
    
    def cancel(self, reason: str = "User requested") -> None:
        """Cancel workflow execution"""
        if self.status not in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
            raise ValueError(f"Cannot cancel workflow in status: {self.status}")
        
        self.status = WorkflowStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        self.error_message = f"Cancelled: {reason}"
        
        # Cancel any running steps
        for step in self.steps:
            if step.status == WorkflowStepStatus.RUNNING:
                step.status = WorkflowStepStatus.SKIPPED
    
    def get_progress_percentage(self) -> float:
        """Calculate workflow progress percentage"""
        if not self.steps:
            return 0.0
        
        completed_steps = sum(1 for step in self.steps 
                            if step.status == WorkflowStepStatus.COMPLETED)
        return min(100.0, (completed_steps / len(self.steps)) * 100)
    
    def get_execution_time_ms(self) -> Optional[int]:
        """Get total execution time in milliseconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return int((end_time - self.started_at).total_seconds() * 1000)
    
    def is_running(self) -> bool:
        """Check if workflow is currently running"""
        return self.status == WorkflowStatus.RUNNING
    
    def is_completed(self) -> bool:
        """Check if workflow is completed (successfully or failed)"""
        return self.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]
    
    def _find_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Find step by ID"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def _check_workflow_completion(self) -> None:
        """Check if all steps are completed and finalize workflow"""
        all_completed = all(step.status == WorkflowStepStatus.COMPLETED 
                           for step in self.steps)
        
        if all_completed:
            self._complete_workflow()
    
    def _complete_workflow(self) -> None:
        """Mark workflow as completed and aggregate results"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        # Aggregate results from all steps
        self.final_result = self._aggregate_step_results()
        
        # Emit completion event
        self.add_event(WorkflowCompletedEvent(
            workflow_id=self.workflow_id,
            final_result=self.final_result,
            execution_time_ms=self.get_execution_time_ms() or 0
        ))
    
    def _fail_workflow(self, error_message: str) -> None:
        """Mark workflow as failed"""
        self.status = WorkflowStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        
        # Emit failure event
        self.add_event(WorkflowFailedEvent(
            workflow_id=self.workflow_id,
            error_message=error_message,
            failed_step=self._get_failed_step_id()
        ))
    
    def _aggregate_step_results(self) -> Dict[str, Any]:
        """Aggregate results from all completed steps"""
        results = {}
        
        for step in self.steps:
            if step.status == WorkflowStepStatus.COMPLETED and step.result:
                results[step.step_id] = step.result
        
        # MVP: Simple aggregation
        if 'calculate' in results:
            final_strategy = results['calculate']
            return {
                'strategy': final_strategy.get('strategy', {}),
                'expected_value': final_strategy.get('expected_value', 0.0),
                'confidence': final_strategy.get('confidence', 0.0),
                'calculation_method': final_strategy.get('calculation_method', 'unknown'),
                'steps_completed': len([s for s in self.steps if s.status == WorkflowStepStatus.COMPLETED]),
                'total_execution_time_ms': self.get_execution_time_ms()
            }
        
        return {'error': 'No calculation results available'}
    
    def _get_failed_step_id(self) -> str:
        """Get the ID of the failed step"""
        for step in self.steps:
            if step.status == WorkflowStepStatus.FAILED:
                return step.step_id
        return "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary for serialization"""
        return {
            'workflow_id': str(self.workflow_id),
            'name': self.name,
            'status': self.status.value,
            'priority': self.priority,
            'progress_percentage': self.get_progress_percentage(),
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'estimated_duration_seconds': self.estimated_duration_seconds,
            'execution_time_ms': self.get_execution_time_ms(),
            'steps': [
                {
                    'step_id': step.step_id,
                    'step_type': step.step_type,
                    'status': step.status.value,
                    'retry_count': step.retry_count
                }
                for step in self.steps
            ],
            'final_result': self.final_result,
            'error_message': self.error_message
        }
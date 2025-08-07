#!/usr/bin/env python3
"""
Quick test to verify all API imports work correctly.
This test bypasses database initialization.
"""

def test_imports():
    """Test that all core components can be imported successfully."""
    print("Testing imports...")
    
    try:
        # Test domain entities
        from src.domain.entities.game import Game, GameStatus
        print("✅ Game entities imported successfully")
        
        from src.domain.entities.strategy import CalculationStatus
        print("✅ Strategy entities imported successfully")
        
        from src.domain.value_objects.difficulty import DifficultyLevel
        print("✅ Difficulty value objects imported successfully")
        
        # Test application queries
        from src.application.queries.game_queries import GetGameByIdQuery
        print("✅ Game queries imported successfully")
        
        from src.application.queries.training_queries import GetTrainingSessionQuery
        print("✅ Training queries imported successfully")
        
        from src.application.queries.analysis_queries import GetAnalysisSessionQuery
        print("✅ Analysis queries imported successfully")
        
        # Test API controllers
        from src.infrastructure.web.api.game_controller import router as game_router
        print("✅ Game controller imported successfully")
        
        from src.infrastructure.web.api.training_controller import router as training_router
        print("✅ Training controller imported successfully")
        
        from src.infrastructure.web.api.analysis_controller import router as analysis_router
        print("✅ Analysis controller imported successfully")
        
        # Test middleware
        from src.infrastructure.web.middleware.auth_middleware import get_current_user
        print("✅ Auth middleware imported successfully")
        
        # Test main app creation (without database)
        print("\n🚀 All imports successful!")
        
        # Get route summary
        print("\nAPI Route Summary:")
        print(f"Game routes: {len(game_router.routes)} endpoints")
        print(f"Training routes: {len(training_router.routes)} endpoints") 
        print(f"Analysis routes: {len(analysis_router.routes)} endpoints")
        
        total_routes = len(game_router.routes) + len(training_router.routes) + len(analysis_router.routes)
        print(f"Total API endpoints: {total_routes}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    exit(0 if success else 1)
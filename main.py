"""
Service Route Optimization
Entry point for the route optimization system.
"""
from config import Config
from services.planner import ServicePlanner


def main():
    config = Config()
    planner = ServicePlanner(config)
    planner.run()


if __name__ == "__main__":
    main()

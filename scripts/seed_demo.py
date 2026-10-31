"""Initialize the local database and create the synthetic company records."""
from agentic_ml_department.db import engine
from agentic_ml_department.models import Base
from agentic_ml_department.seed import seed_demo_data

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print(seed_demo_data(force=False))

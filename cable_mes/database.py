from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

engine = create_engine('sqlite:///cable_mes.db')
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # Import all models here so that they are registered properly on the metadata
    import cable_mes.models
    Base.metadata.create_all(bind=engine)

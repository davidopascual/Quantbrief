from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime


Base = declarative_base()


class Summary(Base):
    __tablename__ = 'summaries'

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    sentiment = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


def init_db(db_path='sqlite:///summarizer.db'):
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


Session = init_db()

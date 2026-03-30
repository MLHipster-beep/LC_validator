from sqlalchemy import Column, String, Integer, create_engine
from sqlalchemy.orm import declarative_base

url = 'sqlite:///databases.db'

engine = create_engine(url)

Base = declarative_base()

class Contact(Base):
    __tablename__=  "contact"
    id = Column(Integer, primary_key= True)
    name = Column(String)
    phone = Column(String)
    message = Column(String)

Base.metadata.create_all(engine)






import sqlalchemy as sql
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class CpuLoads(Base):
    __tablename__ = 'CpuLoads'
    
    r_id = sql.Column('id', sql.Integer, primary_key=True)
    r_value = sql.Column('load', sql.Float, nullable=False)
    r_time = sql.Column('date', sql.String, nullable=False)
    
    sql.Index('date_index', 'date', unique=True)
    
    def __repr__(self) -> str:
        return f'CPU: record_id={self.r_id}, cpu_load={self.r_value}, record_timestamp={self.r_time}.'
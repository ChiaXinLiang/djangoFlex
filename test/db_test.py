import random
import threading
import numpy as np
from PIL import Image
import io
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.mysql import insert

engine = create_engine("mysql+mysqlconnector://root:root@localhost/testing?charset=utf8mb4")


db = declarative_base()

class MyData(db):
    __tablename__ = "mydata"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    age = Column(Integer)
    image = Column(LargeBinary(length=(2**32)-1))

    def __init__(self, id, name, gender, image):
        self.id = id
        self.name = name
        self.gender = gender
        self.image = image

db.metadata.create_all(engine)

def run_testing(id: int, loop_time: int):
    global engine
    Session = sessionmaker(bind=engine)
    session = Session()
    for _ in range(loop_time):
        print("Running", id)
        is_read = random.choice( [True, False] )
        if is_read:
            a = session.query(MyData).filter(MyData.id == id).all()
            if len(a) == 0:
                print( f"[{id}] No data found" )
            else:
                print( f"[{id}] GetData: {a[0].name}" )
        else:
            random_image = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)
            image = Image.fromarray(random_image)
            image_bytes = io.BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes = image_bytes.getvalue()
            name = random.choice( ['John', 'Doe', 'Jane'] )
            age = random.randint( 20, 50 )
            print( f"[{id}] Inserting {name}, {age}" )
            insert_stmt = insert(MyData).values(
                id=id,
                name=name,
                age=age,
                image=image_bytes)
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                name=insert_stmt.inserted.name,
                age=insert_stmt.inserted.age,
                image=insert_stmt.inserted.image,
            )

            session.execute(on_duplicate_key_stmt)
            session.commit()
    session.close()
    print("Finished", id)

t1 = threading.Thread(target=run_testing, args=(1, 100))
t2 = threading.Thread(target=run_testing, args=(2, 100))
t3 = threading.Thread(target=run_testing, args=(3, 100))
t4 = threading.Thread(target=run_testing, args=(4, 100))

t1.start()
t2.start()
t3.start()
t4.start()

t1.join()
t2.join()
t3.join()
t4.join()

print("down")
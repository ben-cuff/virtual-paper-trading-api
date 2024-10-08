from mangum import Mangum
from app.api import app

handler = Mangum(app)

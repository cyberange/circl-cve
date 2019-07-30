import models
import server

server.app.app_context().push()
models.db.init_app(server.app)
models.db.drop_all()
models.db.create_all()
models.Role.insert_roles()

exit()

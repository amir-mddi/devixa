from django.conf import settings

from dealio.project.db_routing import should_read_from_primary


class PrimaryReplicaRouter:
    primary_db = "default"
    replica_db = "replica"

    def db_for_read(self, model, **hints):
        if self.replica_db not in settings.DATABASES:
            return self.primary_db

        if should_read_from_primary():
            return self.primary_db

        return self.replica_db

    def db_for_write(self, model, **hints):
        return self.primary_db

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return db == self.primary_db

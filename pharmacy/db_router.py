class GuestDataRouter:
    """
    Routes GuestPrescriptionRequest to its own SQLite file ('guest_data'),
    completely separate from db.sqlite3. The GitHub-webhook data sync (see
    pharmacy/views_webhook.py) only ever touches db.sqlite3 specifically,
    so keeping guest-submitted data in a different file means it can never
    be wiped out when that sync pulls the pharmacy PC's database.
    """
    guest_models = {'guestprescriptionrequest'}

    def db_for_read(self, model, **hints):
        if model._meta.app_label == 'pharmacy' and model._meta.model_name in self.guest_models:
            return 'guest_data'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == 'pharmacy' and model._meta.model_name in self.guest_models:
            return 'guest_data'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if model_name in self.guest_models:
            return db == 'guest_data'
        if db == 'guest_data':
            return False
        return None

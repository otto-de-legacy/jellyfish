class Task:
    def __init__(self):
        self.id = None
        self.group = None
        self.vertical = None
        self.name = None
        self.color = None
        self.subgroup = None
        self.active_color = None
        self.status = None
        self.app_status = None
        self.status_url = None
        self.status_page_status_code = None
        self.version = None
        self.jobs = []
        self.marathon = Marathon()


class Marathon:
    def __init__(self):
        self.origin = None
        self.instances = None
        self.cpu = None
        self.mem = None
        self.staged = None
        self.running = None
        self.healthy = None
        self.unhealthy = None
        self.marathon_link = None


class Job:
    def __init__(self, name=None, message=None, status=None, stopped=None, started=None, running=None):
        self.name = name
        self.message = message
        self.status = status
        self.stopped = stopped
        self.started = started
        self.running = running

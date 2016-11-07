WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

app_name = "Jellyfish"
navigation_bar = [('views.monitor', 'Status'),
                  ('views.resourcen', 'Resource Allocation'),
                  ('styleguide.style_guide', 'Style Guide')]

THREAD_SUFFIX = "-thread"
THREAD_UPDATE_INTERVAL = 60

config = None
info = None
rdb = None

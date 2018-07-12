from flask_security import login_required, current_user
from flask_appbuilder import fieldwidgets

class Clock(wtf.Form):
    
    @login_required
    def clock_in(wtf.Datetime)

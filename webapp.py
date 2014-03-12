import sys
import web
import yaml
from wtforms import Form, StringField, HiddenField, validators, ValidationError

urls = ("/", "signup")
app = web.application(urls, globals())
render = web.template.render("templates/", base="site")
xrender = web.template.render("templates/")

db = None

@web.memoize
def get_db():
    return web.database(**web.config.db_parameters)

class MultiDict(web.storage):
    def getall(self, name):
        if name in self:
            return [self[name]]
        else:
            return []

class BaseForm(Form):
    def __init__(self, formdata=None, **kwargs):
        formdata = formdata and MultiDict(formdata)
        Form.__init__(self, formdata, **kwargs)

class SignupForm(BaseForm):
    name = StringField('Name', [validators.Required()])
    phone = StringField('Phone Number', [
        validators.Required(), 
        validators.Regexp(r'^\+?[0-9 -]{10,}$', message="That doesn't like a valid phone number.")])
    email = StringField('Email Address', [validators.Required(), validators.Email()])
    address = StringField('Address', [validators.Required()])
    ward = HiddenField()

    def validate_address(self, field):
        print 
        if not self.ward.data:
            raise ValidationError("Please select a place from the dropdown.")

class signup:
    def GET(self):
        form = SignupForm()
        return render.signup(form)

    def POST(self):
        i = web.input()
        print "signup.POST", i
        form = SignupForm(i)
        if form.validate():
            place_id = self.get_place_id(i.ward)
            self.save_volunteer(i, place_id)
            
            send_email(i.email, xrender.email_thankyou(i.name))
            return render.thankyou(i)
        else:
            return render.signup(form)

    def get_place_id(self, path):
        result = get_db().select("places", where="key=$path", vars=locals()) 
        if result:
            return result[0].id
        else:
            return None

    def save_volunteer(self, i, place_id):
        get_db().insert("volunteer_signups", 
            name=i.name, 
            phone=i.phone, 
            email=i.email, 
            address=i.address,
            place_id=place_id)

def check_config():
    if "--config" in sys.argv:
        index = sys.argv.index("--config")
        configfile = sys.argv[index+1]
        sys.argv = sys.argv[:index] + sys.argv[index+2:]
        load_config(configfile)

def load_config(configfile):
    web.config.update(yaml.load(open(configfile)))

def send_email(to_addr, message):
    subject = message.subject.strip()
    message = web.safestr(message)
    if web.config.debug:
        print "To: ", to_addr
        print "Subject: ", subject
        print
        print message
    else:
        web.sendmail(web.config.from_address, to_addr, subject, message)

def main():
    check_config()

    if web.config.get('error_email_recipients'):
        app.internalerror = web.emailerrors(
            web.config.error_email_recipients, 
            app.internalerror, 
            web.config.get('from_address'))

    app.run()


if __name__ == '__main__':
    main()
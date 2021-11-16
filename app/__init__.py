import os, sys, configparser, warnings
from flask import (Flask, redirect, render_template, request, session, url_for)
from app import consent, surveys, mars, rpm, complete, error
from .io import write_metadata
from .utils import gen_code
__version__ = 'mars-irt-validation'

## Define root directory.
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

## Load and parse configuration file.
cfg = configparser.ConfigParser()
cfg.read(os.path.join(ROOT_DIR, 'app.ini'))

## Ensure output directories exist.
data_dir = os.path.join(ROOT_DIR, cfg['IO']['DATA'])
if not os.path.isdir(data_dir): os.makedirs(data_dir)
meta_dir = os.path.join(ROOT_DIR, cfg['IO']['METADATA'])
if not os.path.isdir(meta_dir): os.makedirs(meta_dir)
reject_dir = os.path.join(ROOT_DIR, cfg['IO']['REJECT'])
if not os.path.isdir(reject_dir): os.makedirs(reject_dir)

## Check Flask mode; if debug mode, clear session variable.
debug = cfg['FLASK'].getboolean('DEBUG')
if debug:
    warnings.warn("WARNING: Flask currently in debug mode. This should be changed prior to production.")

## Check Flask password.
secret_key = cfg['FLASK']['SECRET_KEY']
if secret_key == "PLEASE_CHANGE_THIS":
    warnings.warn("WARNING: Flask password is currently default. This should be changed prior to production.")

## Initialize Flask application.
app = Flask(__name__)
app.secret_key = secret_key

## Apply blueprints to the application.
app.register_blueprint(consent.bp)
app.register_blueprint(surveys.bp)
app.register_blueprint(mars.bp)
app.register_blueprint(rpm.bp)
app.register_blueprint(complete.bp)
app.register_blueprint(error.bp)

## Define root node.
@app.route('/')
def index():

    ## Debug mode: clear session.
    if debug:
        session.clear()

    ## Store directories in session object.
    session['data'] = data_dir
    session['metadata'] = meta_dir
    session['reject'] = reject_dir

    ## Record incoming metadata.
    info = dict(
        workerId     = request.args.get('PROLIFIC_PID'),    # Prolific metadata
        assignmentId = request.args.get('SESSION_ID'),      # Prolific metadata
        hitId        = request.args.get('STUDY_ID'),        # Prolific metadata
        subId        = gen_code(24),                        # NivTurk metadata
        address      = request.remote_addr,                 # NivTurk metadata
        browser      = request.user_agent.browser,          # User metadata
        platform     = request.user_agent.platform,         # User metadata
        version      = request.user_agent.version,          # User metadata
        code_success = cfg['PROLIFIC'].get('CODE_SUCCESS', gen_code(8).upper()),
        code_reject  = cfg['PROLIFIC'].get('CODE_REJECT', gen_code(8).upper())
    )

    ## Error-catching: incognito users.
    if not 'workerId' in session and info['workerId'] in os.listdir(meta_dir):

        ## Find and grab subId from log file.
        with open(os.path.join(session['metadata'], info['workerId']),'r') as f:
            for line in f.readlines():
                if 'subId' in line:
                    info['subId'] = line.strip().split('\t')[-1]
                    break

        ## Update metadata.
        session['WARNING'] = 'Suspected incognito user.'

    ## Case 1: workerId absent.
    if info['workerId'] is None:

        ## Redirect participant to error (missing workerId).
        return redirect(url_for('error.error', errornum=1000))

    ## Case 2: mobile user.
    elif info['platform'] in ['android','iphone','ipad','wii']:

        ## Redirect participant to error (platform error).
        return redirect(url_for('error.error', errornum=1001))

    ## Case 3: repeat visit, previous reject.
    elif (f'%s_surveys.json' %info['subId'] in os.listdir(reject_dir)) or \
         (f'%s_mars.json' %info['subId'] in os.listdir(reject_dir)) or \
         (f'%s_rpm.json' %info['subId'] in os.listdir(reject_dir)) or \
         ('complete' in session and session['complete'] == 'reject'):

        ## Update metadata.
        for k, v in info.items(): session[k] = v
        session['complete'] = 'reject'

        ## Redirect participant to complete page.
        return redirect(url_for('complete.complete'))

    ## Case 4: repeat visit, previous success.
    elif (f'%s_rpm.json' %info['subId'] in os.listdir(data_dir)) or \
         ('complete' in session and session['complete'] == 'success'):

        ## Update metadata.
        for k, v in info.items(): session[k] = v
        session['complete'] = 'success'

        ## Redirect participant to complete page.
        return redirect(url_for('complete.complete'))

    ## Case 5: repeat visit, previously completed MARS experiment.
    elif f'%s_mars.json' %info['subId'] in os.listdir(data_dir):

        ## Update metadata.
        for k, v in info.items(): session[k] = v

        ## Redirect participant to complete page.
        return redirect(url_for('rpm.rpm'))

    ## Case 6: repeat visit, previously completed surveys.
    elif f'%s_surveys.json' %info['subId'] in os.listdir(data_dir):

        ## Update metadata.
        for k, v in info.items(): session[k] = v

        ## Redirect participant to complete page.
        return redirect(url_for('mars.mars'))

    ## Case 7: repeat visit, preexisting activity.
    elif 'workerId' in session:

        ## Redirect participant to consent form.
        return redirect(url_for('consent.consent'))

    ## Case 7: first visit, workerId present.
    else:

        ## Update metadata.
        for k, v in info.items(): session[k] = v
        write_metadata(session, ['workerId','hitId','assignmentId','subId','address','browser','platform','version'], 'w')

        ## Flag incognito users.
        if 'WARNING' in session:
             write_metadata(session, ['WARNING'], 'a')

        ## Redirect participant to consent form.
        return redirect(url_for('consent.consent'))
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector as ms
import os
import replicate
from io import BytesIO



cnx = ms.connect(user='magic_register', password='Indira@2000',
                 host='185.104.29.84', database='magic_register')
cursor = cnx.cursor()


# Setting the Environment of the application using the API token of Replicate from the database
get_API_key_query = "SELECT `API_KEY` FROM `whisper_config`"
cursor.execute(get_API_key_query)
get_API_key = cursor.fetchone()[0]

os.environ['REPLICATE_API_TOKEN'] = str(get_API_key)

# Closing the DB Connection
cursor.close()
cnx.close()

app = Flask(__name__, static_url_path='/static')
app.secret_key = 'my-secret-key'


@app.route("/")
# @app.route("/login")
def login():
    return render_template('login.html')


@app.route("/", methods=['POST', 'GET'])
def Authenticate():
    # connecting to database...
    cnx = ms.connect(user='magic_register', password='Indira@2000',
                     host='185.104.29.84', database='magic_register')
    cursor = cnx.cursor()

    email = request.form['email']
    login_code = request.form['login_code']

    # You can add code here to validate the user's login information
    check_for_cred = f"SELECT `phytonlogin` FROM `user` WHERE `email` = '{email}'"
    cursor.execute(check_for_cred)
    session['get_user_email'] = email

    auth_code = cursor.fetchone()[0]
    
    cursor.close()
    cnx.close()
    if login_code != auth_code:
        return render_template("login.html", data="Incorrect Email or Password")
    else:
        return redirect(url_for('Dashboard'))


@app.route('/logout')
def logout():
    session.pop('get_user_email', None)  # remove the email from the session
    return redirect(url_for('login'))

admin_name_validation = ""
@app.route("/dashboard")
def Dashboard():
    if 'get_user_email' in session:
        cnx = ms.connect(user='magic_register', password='Indira@2000',
                         host='185.104.29.84', database='magic_register')
        cursor = cnx.cursor()
        email = session.get("get_user_email")

        ########## Getting the User data using Email from database ###########
        name_query = f"SELECT `name` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(name_query)
        name = cursor.fetchone()[0]
        global admin_name_validation
        admin_name_validation = name

        # Subscription Details
        subscription_end_query = f"SELECT `end_subscription_period` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(subscription_end_query)
        subscription_end = cursor.fetchone()[0]

        # Words Usage
        # words_total_query = f"SELECT `words_total` FROM `user` WHERE `email` = '{email}'"
        # cursor.execute(words_total_query)
        # words_total = cursor.fetchone()[0]

        # words_count_query = f"SELECT `words_count` FROM `user` WHERE `email` = '{email}'"
        # cursor.execute(words_count_query)
        # words_count = cursor.fetchone()[0]

        # Image Usage
        # images_total_query = f"SELECT `images_total` FROM `user` WHERE `email` = '{email}'"
        # cursor.execute(images_total_query)
        # images_total = cursor.fetchone()[0]

        # images_count_query = f"SELECT `images_count` FROM `user` WHERE `email` = '{email}'"
        # cursor.execute(images_count_query)
        # images_count = cursor.fetchone()[0]

        # Tmporary Things
        words_total = 20000
        words_count = 0
        images_total = 20
        images_count = 0


        #Minutes Usage Whisper
        minutes_total_query = f"SELECT `minutes_total` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(minutes_total_query)
        minutes_total = cursor.fetchone()[0]

        minutes_count_query = f"SELECT `minutes_count` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(minutes_count_query)
        minutes_count = cursor.fetchone()[0]
        minutes_to_show = custom_round(minutes_count)

        cursor.close()
        cnx.close()
        return render_template("dashboard.html", data={'name': name, 'subscription_end': subscription_end, 'words_total': words_total, 'words_count': words_count, 'images_total': images_total, 'images_count': images_count, 'minutes_total':minutes_total, 'minutes_count':minutes_to_show})

    else:
        return redirect(url_for("login"))


############################### Whisper AI Functions ######################################

from decimal import Decimal

def custom_round(num, digits=2, Isstr=False):
    tmp = Decimal(num)
    x = ("{0:.%sf}" % digits).format(round(tmp, digits))
    if Isstr:
        return x
    return float(Decimal(x))

@app.route('/whisper')
def Whisper():
    if 'get_user_email' in session:
        cnx = ms.connect(user='magic_register', password='Indira@2000',
                         host='185.104.29.84', database='magic_register')
        cursor = cnx.cursor()

        email = session['get_user_email']
        minutes_count_query = f"SELECT `minutes_count` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(minutes_count_query)
        minutes_count = cursor.fetchone()[0]
        minutes_to_show = custom_round(minutes_count)

        minutes_total_query = f"SELECT `minutes_total` FROM `user` WHERE `email` = '{email}'"
        cursor.execute(minutes_total_query)
        minutes_total = cursor.fetchone()[0]

        cursor.close()
        cnx.close()
        return render_template('whisper.html', data=[minutes_to_show, minutes_total])

    else:
        return redirect(url_for("login"))


# Audio Upload through Mic
audioRecordedGlobal = None
@app.route('/upload', methods=['POST'])
def upload():
    audio = request.files.get('audio').read()
    # print(audio)
    global audioRecordedGlobal
    audioRecordedGlobal = audio
    return "Done"


minutes_to_update = 0
@app.route('/duration', methods=['POST'])
def duration():
    global minutes_to_update
    minutes_to_update = request.json['duration']
    # do something with the duration data
    return 'OK'



@app.route('/whisper-results', methods=["POST"])
def WhisperAI():
    cnx = ms.connect(user='magic_register', password='Indira@2000',
                     host='185.104.29.84', database='magic_register')
    cursor = cnx.cursor()
    email = session['get_user_email']

    minutes_count_query = f"SELECT `minutes_count` FROM `user` WHERE `email` = '{email}'"
    cursor.execute(minutes_count_query)
    minutes_count = float(cursor.fetchone()[0])

    minutes_total_query = f"SELECT `minutes_total` FROM `user` WHERE `email` = '{email}'"
    cursor.execute(minutes_total_query)
    minutes_total = cursor.fetchone()[0]

    # Reading the audio file and Converting the audio file in Bytes
    audioFile = BytesIO(request.files['audioFile'].read())
    # Or
    # Taking mic input
    audioRecords = BytesIO(audioRecordedGlobal)

    # language = request.form['language']
    to_translate = request.form.get('to_translate') == 'on'

    # Model Configuration Fetching from database
    # model = DBRead('whisper_config','model')
    transcription = DBRead('whisper_config','transcription')
    # temp = DBRead('whisper_config','temperature')
    # # patience = DBRead('whisper_config','patience')
    # suppress = DBRead('whisper_config','suppress_tokens')
    # temperature = DBRead('whisper_config','temp_increment_on_fallback')
    # compression = DBRead('whisper_config','compression_ratio_threshold')
    # logprob = DBRead('whisper_config','logprob_threshold')
    # nospeech = DBRead('whisper_config','no_speech_threshold')
    # print(minutes_to_update)
    global minutes_to_update
    minutes_to_update = custom_round(minutes_to_update)
    print("Uploaded Audio or File Size : ",minutes_to_update)

    if minutes_count <= float(minutes_total):
        if len(audioFile.read()) != 0:
            # Model Running
            try: 
                output = replicate.run("openai/whisper:e39e354773466b955265e969568deb7da217804d8e771ea8c9cd0cef6591f8bc",
                                    input={"audio": audioFile,
                                            # "model": model,
                                            "transcription": transcription,
                                            "translate": to_translate,
                                            #   "language": language,
                                            # "temperature": int(temp),
                                            # #   "patience": float(patience),
                                            # "suppress_tokens": suppress,
                                            # #   "initial_prompt": "",
                                            #   "condition_on_previous_text": False,
                                            # "temperature_increment_on_fallback": float(temperature),
                                            # "compression_ratio_threshold": float(compression),
                                            # "logprob_threshold": int(logprob),
                                            # "no_speech_threshold": float(nospeech)
                                            })

                update_minutes_query = f"UPDATE `user` SET `minutes_count` = '{minutes_to_update+minutes_count}' WHERE `email` = '{email}';"
                cursor.execute(update_minutes_query)
                cnx.commit()
                cursor.close()
                cnx.close()
                print("The total minutes will be : ",minutes_count+minutes_to_update)
                minutes_to_show = str(minutes_count+minutes_to_update)
                return render_template('whisper-results.html', data=[output['transcription'], output['translation'], output['detected_language'], minutes_to_show[0:5], minutes_total])
            except Exception as e:
                print(e)
                return render_template("whisper-results.html",data=["There is some problems in AI Model or Your File Size is too large","","",minutes_count,minutes_total])
            # return render_template('whisper.html',data=["","","","","",""])

        else:
            # Model Running
            try:
                output = replicate.run("openai/whisper:e39e354773466b955265e969568deb7da217804d8e771ea8c9cd0cef6591f8bc",
                                    input={"audio": audioRecords,
                                            # "model": model,
                                            "transcription": transcription,
                                            "translate": to_translate,
                                            # #   "language": language,
                                            # "temperature": int(temp),
                                            # #   "patience": float(patience),
                                            # "suppress_tokens": suppress,
                                            # #   "initial_prompt": "",
                                            # #   "condition_on_previous_text": False,
                                            # "temperature_increment_on_fallback": float(temperature),
                                            # "compression_ratio_threshold": float(compression),
                                            # "logprob_threshold": int(logprob),
                                            # "no_speech_threshold": float(nospeech)
                                             })

                update_minutes_query = f"UPDATE `user` SET `minutes_count` = '{minutes_to_update+minutes_count}' WHERE `email` = '{email}';"
                cursor.execute(update_minutes_query)
                cnx.commit()
                cursor.close()
                cnx.close()
                print("The total minutes will be : ",minutes_count+minutes_to_update)
                minutes_to_show = str(minutes_count+minutes_to_update)
                return render_template('whisper-results.html', data=[output['transcription'], output['translation'], output['detected_language'], minutes_to_show[0:5], minutes_total])
            
            except Exception as e:
                print(e)
                return render_template("whisper-results.html",data=["There is some problems in AI Model or Your Audio Record is too large","","",minutes_count,minutes_total])

    else:
        return render_template('whisper-results.html', data=["", "", "", "", "", "You Have Used All Your Minutes"])

########## Admin Panel ###########

# Utility function for updating the form data to database
def DBUpdate(table, field, value):
    cnx = ms.connect(user='magic_register', password='Indira@2000',
                     host='185.104.29.84', database='magic_register')
    cursor = cnx.cursor()
    query = f"UPDATE `{table}` SET `{field}` = '{value}'"
    cursor.execute(query)
    cnx.commit()
    cursor.close()
    cnx.close()

def DBRead(table,field):
    cnx = ms.connect(user='magic_register', password='Indira@2000',
                     host='185.104.29.84', database='magic_register')
    cursor = cnx.cursor(buffered=True)
    query = f"SELECT `{field}` FROM `{table}`"
    cursor.execute(query)
    data = cursor.fetchone()[0]
    cursor.close()
    cnx.close()
    return data


@app.route('/admin',methods=['GET'])
def Admin():
    if 'get_user_email' in session: 
        if 'Admin' == admin_name_validation:
            #Get the Data
            api_key = DBRead('whisper_config','API_Key')
            model = DBRead('whisper_config','model')
            transcription = DBRead('whisper_config','transcription')
            temp = DBRead('whisper_config','temperature')
            patience = DBRead('whisper_config','patience')
            suppress = DBRead('whisper_config','suppress_tokens')
            temperature = DBRead('whisper_config','temp_increment_on_fallback')
            compression = DBRead('whisper_config','compression_ratio_threshold')
            logprob = DBRead('whisper_config','logprob_threshold')
            nospeech = DBRead('whisper_config','no_speech_threshold')

            # data = [api_key,model,transcription,temp,patience,suppress,temperature,compression,logprob,nospeech]
            
            return render_template('admin.html',data = [api_key,transcription,temp,patience,suppress,temperature,compression,logprob,nospeech,model])

        else:
            return(redirect('/dashboard'))
    
    else:
        return redirect(url_for('login.html'))


@app.route('/admin-success', methods=["POST"])
def AdminWhisper():
    # Form Data
    API_Key = request.form['API_Key']
    Transcription = request.form['Transcription']
    Temperature = request.form['Temperature']
    Patience = request.form['Patience']
    Suppress_Tokens = request.form['Suppress_Tokens']
    Temperature_increment = request.form['Temperature_increment']
    Compression = request.form['Compression']
    Logprob = request.form['Logprob']
    Speech = request.form['Speech']
    Model = request.form['Model']

    # Updation Database Queries and Executing Queries
    DBUpdate('whisper_config','API_Key',API_Key)
    DBUpdate('whisper_config','transcription',Transcription)
    DBUpdate('whisper_config','temperature',Temperature)
    DBUpdate('whisper_config','patience',Patience)
    DBUpdate('whisper_config','suppress_tokens',Suppress_Tokens)
    DBUpdate('whisper_config','temp_increment_on_fallback',Temperature_increment)
    DBUpdate('whisper_config','compression_ratio_threshold',Compression)
    DBUpdate('whisper_config','logprob_threshold',Logprob)
    DBUpdate('whisper_config','no_speech_threshold',Speech)
    DBUpdate('whisper_config','model',Model)

    # print(API_Key,Transcription,Temperature,Patience,Suppress_Tokens,Temperature_increment,Compression,Logprob,Speech,Model)
    return redirect('/admin')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server(e):
    return render_template('500.html'), 500


if __name__ == "__main__":
    app.run(port=5000,debug=True)

# threaded=True
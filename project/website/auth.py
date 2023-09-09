from flask import Blueprint, flash , render_template , request , redirect, url_for,send_file
from .models import User ,original_sentence,Annotated,CurrentProgress
from . import db
import os
import urllib.parse
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from sqlalchemy import create_engine ,text
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd

auth_blueprint = Blueprint('auth',__name__)
@auth_blueprint.route("/", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user:
            if check_password_hash(user.password, password):
                login_user(user, remember=True)
                if user.role == 'admin':
                    flash('Logged in successfully!', category='success')
                    return render_template("admin.html", user=current_user,name=username)
                elif user.role == 'annotator':
                    flash('Logged in successfully!', category='success')
                    return redirect(url_for('view.annotate'))
            else:
                flash('Incorrect  password. Please try again.', category='error')
        else:
            flash('User does not exist.', category='error')

    return render_template("login.html", user=current_user)

 
@auth_blueprint.route("/logout")
@login_required           
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_blueprint.route('/admin', methods=['GET','POST'])
@login_required
def admin():
    if request.method == 'POST':
        if 'login_submit' in request.form:
            username = request.form.get('username')
            role = request.form.get('role')
            password = request.form.get('password')
           
            user = User.query.filter_by(username=username).first()
            if user:
                flash('User already exists.', category='error')
            else:
                    if len(password) < 7:
                        flash('Password must be greater than 7 characters', category='error')
                    else:
                        new_user = User(username=username, role=role, password=generate_password_hash(password, method='sha256'))
                        db.session.add(new_user)
                        db.session.commit()
                        progress = CurrentProgress(user_id=new_user.id, no_of_tagged=0, last_status=True)
                        db.session.add(progress)
                        db.session.commit()

                        login_user(new_user, remember=True)
                        flash('Account created!', category='success')
                    return redirect(url_for('auth.admin'))
        elif 'other_form' in request.form:
            file = request.files['file']
            try:
                df = pd.read_excel(file)
                new_col = []
                word_col = []
                var = (df.iloc[:,2])
                for j in var:
                    j = j.replace('[(','')
                    j = j.replace('(','')
                    j = j.replace(')','')
                    j = j.replace(']','')
                    j = j.replace('[','')
                    j = j.replace(')]','')
                    j = j.replace("('",'')
                    j = j.replace("'(",'')
                    my_list = [item.strip() for item in j.split(',') if item.strip() != '']
                    sent = ""
                    words = ""
                    ind = 0
                    new_list = []
                    for i in range(len(my_list)):
                        if(i<len(my_list)-1):
                            if(my_list[i]==my_list[i+1]):
                                i = i+2
                                continue
                        new_list.append(my_list[i])
                    for k in new_list:
                        k = k.replace("'","")
                        if(ind==0):
                            words = words + k + " "
                            ind = 1
                            continue
                        sent = sent + k + " "
                        ind = 0
                    word_col.append(words)
                    new_col.append(sent)
                df = df.assign(lang_tag=new_col,inplace=True)  
                df['annotation_status'] = False
                df['no_of_words']= df['comments'].str.split(" ").str.len()
                df['progress']=0
                df.drop(df.columns[0], axis = 1, inplace = True )
                db.session.bulk_insert_mappings(
                    original_sentence,
                    df.to_dict(orient='records')
                )
                db.session.commit()
                flash('File successfully uploaded', category='success')
                return render_template('admin.html', msg = 'File successfully uploaded')
            except SQLAlchemyError as e:
                db.session().rollback()
                flash('Error while uploading file', category='error')
                print(e)
                return render_template('admin.html', msg = 'Error while uploading file')
               
           
    return render_template("admin.html")


@auth_blueprint.route('/showme', methods=['GET'])
@login_required
def showme():
    if request.method == 'GET':
        annotators = User.query.filter_by(role='annotator').all()
        if not annotators:
            flash('Add some annotators !', category='error')
            
    return render_template('habibi.html', annotators=annotators)

@auth_blueprint.route('/download', methods=['GET'])
@login_required
def download():
    if request.method == 'GET':
            with db.engine.connect() as conn:
                        query = text("select * from original_sentence ORDER BY sentence_index")
                        result = conn.execute(query)
                        row= result.fetchall()
                        query2 = text("select * from annotated ORDER BY sent_id")
                        result2 = conn.execute(query2)
                        row2= result2.fetchall()
                        df2 = pd.DataFrame(row2,columns=['annotation_id','sent_id','pos_tag','new_lang_tag','user_id'])
                        df = pd.DataFrame(row,columns=['id','comments','comments_tagged','lang_tag','annotation_status','no_of_words','progress'])
                        df.drop(df.columns[4], axis = 1, inplace = True )
                        df.drop(df.columns[4], axis = 1, inplace = True )
                        df.drop(df.columns[4], axis = 1, inplace = True )
                        df["new_lang_tag"]=df2['new_lang_tag']
                        df["pos_tag"]=df2['pos_tag']
                        df['new_comments']=None
                        for i in range(len(df2)):

                            com=df['comments'][i].split(" ")
                            lang=df['new_lang_tag'][i].split(" ")
                            pos=df['pos_tag'][i]   
                            if pos:
                               pos=pos.split(" ")
                               final=list(zip(com,lang,pos))
                               df.at[i, "new_comments"] = final
                        website_folder = os.path.join(os.getcwd(), 'website')
                        excel_file_path = os.path.join(website_folder, 'output.xlsx')
                        excel_writer = pd.ExcelWriter(excel_file_path, engine='xlsxwriter')
                        df.to_excel(excel_writer, sheet_name='Data', index=False)
                        excel_writer.close()  
                        # Construct the relative path to download the file
                        relative_path_to_download = os.path.join('output.xlsx')

                        encoded_path = urllib.parse.quote(relative_path_to_download)
                        
                        # Send the file for download
                        return send_file(encoded_path, as_attachment=True)


    return render_template('admin.html', msg = 'File successfully downloaded')
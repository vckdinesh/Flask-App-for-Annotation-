from flask_sqlalchemy import SQLAlchemy
import pandas as pd
from flask import Flask, render_template, request , Blueprint , flash,redirect,url_for
from flask_login import login_user, login_required, logout_user, current_user
from fileinput import filename
from . import db
from sqlalchemy import create_engine ,text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import create_engine
from os import environ
import numpy as np

USERNAME = environ.get('usr')
PASSWORD = environ.get('pass')
IP_ADDR = environ.get('db_ip')
DB_NAME = environ.get('db_name')
engine = create_engine(f'postgresql://{USERNAME}:{PASSWORD}@{IP_ADDR}/{DB_NAME}')

view_blueprint = Blueprint('view',__name__)
@view_blueprint.route('/annotate', methods=['GET', 'POST'])
@login_required
def annotate():
    if request.method == 'GET':
            with db.engine.connect() as conn:
              query=text("SELECT * FROM current_progress WHERE user_id = :uid;")
              params = {"uid":current_user.get_id()}
              result = conn.execute(query,params)
              row = result.fetchone()
              status=row[3]
              aid=row[1]
              if status == 0:
                query = text("SELECT * FROM annotated WHERE annotation_id = :aid;")
                params = {"aid":aid}
                result = conn.execute(query,params)
                row3= result.fetchone()
                sid = row3[1]
                lang=row3[3].split(" ")
                query2 = text("SELECT * FROM original_sentence WHERE sentence_index= :sid;")
                params2 = {"sid":sid}
                result2 = conn.execute(query2,params2)
                result3 = conn.execute(query2,params2)
                if result2:
                    row2 = result2.fetchone()
                    # print(row)
                    words = row2[1].split(" ")
                    if row3[2]:
                        pos=row3[2].split(" ")
                    else:
                        pos = [""] * len(words)
                    final3 = zip(words,lang,pos)
                    query3 = text("select no_of_tagged from current_progress where user_id = :uid;")
                    params3 = {"uid":current_user.get_id()}
                    result4=conn.execute(query3, params3)
                    row5=result4.fetchone()
                    tag=row5[0]
                    return render_template("annotate.html",user=current_user, final = final3 , result = result3 , sent = sid,tag=tag)
                else:
                    flash('No sentence to annotate', category='error')
                    return render_template("annotate.html", user=current_user)
              elif status == 1:
                query = text("SELECT * FROM original_sentence WHERE annotation_status = false and progress = 0 LIMIT 1;")
                result = conn.execute(query)
                result3 = conn.execute(query)
                row = result.fetchone()
                if row:
                        sid=row[0]
                        sent = row[1].replace("\n","")
                        words = sent.split(" ")
                        lang = row[3].split(" ")
                        final = zip(words, lang)
                        query = text("INSERT INTO annotated (sent_id,new_lang_tag,user_id) VALUES (:sid,:lang,:uid);")
                        params = {"sid":row[0],"uid":current_user.get_id(),"lang": row[3]}
                        conn.execute(query, params)
                        conn.commit()
                        query = text("SELECT annotation_id FROM annotated WHERE sent_id = :sid;")
                        params = {"sid":row[0]}
                        result = conn.execute(query, params)
                        row2 = result.fetchone()
                        query = text("UPDATE current_progress SET last_tagged_id = :sid , last_status = :stat where user_id = :uid;")
                        param = {"sid":row2[0],"stat":False,"uid":current_user.get_id()}
                        result = conn.execute(query, param)
                        conn.commit()
                        query = text("UPDATE original_sentence SET progress = 1 where sentence_index = :sid;")
                        param = {"sid":sid,}
                        result = conn.execute(query, param)
                        conn.commit()
                        query3 = text("select no_of_tagged from current_progress where user_id = :uid;")
                        params3 = {"uid":current_user.get_id()}
                        result4=conn.execute(query3, params3)
                        row5=result4.fetchone()
                        tag=row5[0]
                        conn.commit()
                        return render_template("annotate.html", sent = row[0] ,result=result3, final=final, user=current_user,tag=tag) 
                else:
                    flash('No sentence to annotate', category='error')
                    return render_template("annotate.html", user=current_user)


    
@view_blueprint.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.form.get("Save") == "Save": 
            sid = request.form.get('sid')
            lang = request.form.getlist('lang')
            lang = [lang.strip() for lang in lang]
            pos = request.form.getlist('pos')
            pos = [pos.strip() for pos in pos]
            newlang = ' '.join(map(str, lang))
            newpos = ' '.join(map(str, pos))
            # print(sid)
            # print(newlang)
            # print(pos)
            # print(newpos)
            with db.engine.connect() as conn:
                query = text("UPDATE annotated SET pos_tag = :pos , new_lang_tag = :lang WHERE sent_id = :sid;")
                params = {"pos":newpos,"lang":newlang,"sid":sid}
                conn.execute(query, params)
                query1 = text("SELECT * from original_sentence WHERE sentence_index = :sid;")
                param = {"sid":sid}
                result = conn.execute(query1, param)
                result3 = conn.execute(query1, param)
                row = result.fetchone()
                new_progress = text("UPDATE ")
                words = row[1].split(" ")
                final = zip(words,lang,pos)
                query2 = text("SELECT no_of_tagged from current_progress WHERE user_id = :uid;")
                params = {"uid":current_user.get_id()}
                result = conn.execute(query2, params)
                newrow = result.fetchone()
                # print(newrow[0])
                # print(current_user.get_id())
                new_tag_num = newrow[0]+1
                length_pos = len(pos)-pos.count("")
                length_words = len(words)-words.count("")
                query3 = text("select no_of_tagged from current_progress where user_id = :uid;")
                params3 = {"uid":current_user.get_id()}
                result4=conn.execute(query3, params3)
                row5=result4.fetchone()
                tag=row5[0]
                conn.commit()



            flash( 'Saved Successfully', category='success')
            return render_template("annotate.html",user=current_user, final = final , result = result3 , sent = sid,tag=tag)
    if request.form.get("next") == "next":
        lang = request.form.getlist('lang')
        lang = [lang.strip() for lang in lang]
        pos = request.form.getlist('pos')
        pos = [pos.strip() for pos in pos]
        sid = request.form.get('sid')
        newlang = ' '.join(map(str, lang))
        newpos = ' '.join(map(str, pos))
        # print(sid)
        # print(newlang)
        # print(pos)
        # print(newpos)
        with db.engine.connect() as conn:
            query1 = text("SELECT * from original_sentence WHERE sentence_index = :sid;")
            param = {"sid":sid}
            result = conn.execute(query1, param)
            result3 = conn.execute(query1, param)
            row = result.fetchone()
            conn.commit()
            
        words = row[1].split(" ")
        # print(words)
        length_pos = len(pos)-pos.count("")
        length_words = len(words)-words.count("")
        length_lang = len(lang)-lang.count("")

        # print(length_pos)
        # print(length_words)
        final = zip(words,lang,pos)
        if(length_pos!=length_words):
            flash( 'Please fill all the respctive pos tags', category='error')
            return render_template("annotate.html",user=current_user, final = final , result = result3 , sent = sid)
        elif(length_lang!=length_words):
            flash( 'Please fill all the respctive language tags', category='error')
            return render_template("annotate.html",user=current_user, final = final , result = result3 , sent = sid)
        else:
            with db.engine.connect() as conn:
                query = text("UPDATE annotated SET pos_tag = :pos , new_lang_tag = :lang WHERE sent_id = :sid;")
                params = {"pos":newpos,"lang":newlang,"sid":sid}
                conn.execute(query, params)
                query2 = text("SELECT no_of_tagged from current_progress WHERE user_id = :uid;")
                params = {"uid":current_user.get_id()}
                result = conn.execute(query2, params)
                newrow = result.fetchone()
                conn.commit()
                # print(newrow[0])
                # print(current_user.get_id())
                new_tag_num = newrow[0] + 1
                # print(new_tag_num)
            try:
                with db.engine.connect() as conn:
                    query = text("SELECT * FROM annotated where sent_id = :sid;")
                    param = {"sid":sid}
                    result = conn.execute(query, param)
                    row = result.fetchone()
                    aid = row[0]
                    query = text("UPDATE original_sentence SET annotation_status = true WHERE sentence_index = :sid;")
                    param = {"sid":sid}
                    result = conn.execute(query, param)
                    query = text("UPDATE current_progress SET last_tagged_id = :aid , last_status = :stat , no_of_tagged = :num where user_id = :uid;")
                    param = {"aid":aid,"stat":True,"num":new_tag_num,"uid":current_user.get_id()}
                    result = conn.execute(query, param)
                    conn.commit()
                    return redirect(url_for('view.annotate'))
            except SQLAlchemyError as e:
                return (e)
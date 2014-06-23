import psycopg2, psycopg2.extras, collections
import json

from flask import Flask
from flask import request
from flask import jsonify
from flask import session
from flask.views import MethodView

#HELPER#
from ..helper import *
#from ..helper.Database import sql

class Event(MethodView):

    def get(self):
        facebookId = session['idFacebook']
        try:
            cur = sql.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            #cur = sql.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
            #cur = sql.cursor()
            cur.execute("""SELECT evento.id_evento, party.nome_evento, party.admin, party.data, party.num_utenti
                        FROM evento 
                        JOIN party ON evento.id_evento=party.id_evento 
                        JOIN utenti ON utenti.id_user=evento.id_user 
                        WHERE utenti.id_user=%s""",
                        (facebookId,))
            sql.commit()
            eventi = cur.fetchall()
            
        except Exception, e:
            sql.rollback()
            return 'error '+str(e)
        finally:
            cur.close()
        return jsonify(results = eventi)

    def post(self):
        if request.form['name']!='' and request.form['userList']!='':
            try:
                nome_evento = request.form['name'].strip()
                userList = json.loads(request.form['userList'].strip())
                admin = session['idFacebook'].strip()
            except:
                return 'error json parser'

            #print nome_evento

            if not admin in userList:
                userList.append(admin)

            #print 'USERLIST: '+str(userList)

            numUtenti = len(userList)
            try:
                cur = sql.cursor()
                cur.execute("INSERT INTO party(admin,nome_evento) VALUES(%s,%s) RETURNING id_evento",(admin,nome_evento))
                
                eventId = str(cur.fetchone()[0])
                for p in userList:
                    print str(p)
                    cur.execute("INSERT INTO evento(id_evento, id_user) VALUES (%s,%s)", (eventId,p))

                    
                    #int id, String name, String details, String date, String admin, int numUtenti
                sql.commit()

                adminName = getFacebookName(admin)
                msg = {'type':'newEvent','id_evento': eventId, 'nome_evento': nome_evento, 'admin': admin, 'adminName': adminName, 'num_utenti': str(numUtenti)}
                sendNotificationEvent(eventId,admin,msg)
                    
                    #ris = sendNotification(str(p),msg)
                    #if ris is not None:
                    #    print 'GCM error: '+str(ris)
            except Exception, e:
                sql.rollback()
                return 'error1 '+str(e)
            finally:
                cur.close()     
            
            return eventId
        else:
            return 'error POST parameters'

    def delete(self,idEvento):

        user = session['idFacebook']
        
        try:
            cur = sql.cursor()
            cur.execute("SELECT admin FROM party WHERE id_evento=%s",(idEvento,))
            admin = cur.fetchone()[0]
            sql.commit()

            if user==admin :
                cur.execute("DELETE FROM party WHERE id_evento=%s", (eventId,))

            else:
                delUtenteFromEvent(idEvento,user)

            #adminName = getFacebookName(admin)
            #msg = {'type':'newEvent','id_evento': eventId, 'nome_evento': nome_evento, 'admin': admin, 'adminName': adminName, 'num_utenti': str(numUtenti)}
            #sendNotificationEvent(eventId,admin,msg)
        
            return 'fatto'

        except Exception, e:
            sql.rollback()
            return 'error '+str(e)
        finally:
            cur.close()     
        
        
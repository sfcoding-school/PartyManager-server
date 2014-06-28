import psycopg2
import psycopg2.extras
import json

from flask import request
from flask import jsonify
from flask import session
from flask.views import MethodView
from flask import current_app as app

#HELPER#
from ..helper import *
#from ..helper.Database import sql
#from  ..main import log


class Event(MethodView):

    def get(self):
        app.logger.info('Get Event')
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
            return 'error ' + str(e)
        finally:
            cur.close()
        return jsonify(results=eventi)

    def post(self):
        if request.form['name'] != '' and request.form['userList'] != '':
            try:
                nome_evento = request.form['name'].strip()
                userList = json.loads(request.form['userList'].strip())
                admin = session['idFacebook'].strip()
            except:
                return 'error json parser'

            # print nome_evento

            if not admin in userList:
                userList.append(admin)

            # print 'USERLIST: '+str(userList)

            numUtenti = len(userList)
            try:
                cur = sql.cursor()
                cur.execute(
                    "INSERT INTO party(admin,nome_evento) VALUES(%s,%s) RETURNING id_evento", (admin, nome_evento))

                eventId = str(cur.fetchone()[0])
                for p in userList:
                    # print str(p)
                    cur.execute(
                        "INSERT INTO evento(id_evento, id_user) VALUES (%s,%s)", (eventId, p))

                    # int id, String name, String details, String date, String admin, int
                    # numUtenti
                sql.commit()

                adminName = getFacebookName(admin)
                msg = {'type': CODE.t['event'],
                       'method': CODE.m['new'],
                       'id_evento': eventId,
                       'nome_evento': nome_evento,
                       'admin': admin,
                       'adminName': adminName,
                       'num_utenti': str(numUtenti)
                       }

                sendNotificationEvent(eventId, admin, msg)

                    #ris = sendNotification(str(p),msg)
                    # if ris is not None:
                    #    print 'GCM error: '+str(ris)
            except Exception, e:
                sql.rollback()
                return 'error1 ' + str(e)
            finally:
                cur.close()

            return eventId
        else:
            return 'error POST parameters'

    def put(self, idEvento):
        user = session['idFacebook']
        nomeEvento = request.form.get('name')
        if nomeEvento == '':
            app.logger.warning('nome evento errato')
            return 'nome evento errato'
        app.logger.info('MODIFICA NOME EVENTO')

        try:
            cur = sql.cursor()
            admin = Database.getAdminOfEvent(idEvento)

            if user == admin and nomeEvento:
                nomeEventoVecchio = Database.getEventName(idEvento)
                app.logger.debug('modifca nome admin')
                cur.execute(
                    "UPDATE party SET nome_evento=%s WHERE id_evento=%s", (nomeEvento, idEvento,))
                msg = {'type': CODE.t['event'],
                       'method': CODE.m['mod'],
                       'id_evento': str(idEvento),
                       'nome_evento_vec': nomeEventoVecchio,
                       'nome_evento': nomeEvento,
                       'admin_name': getFacebookName(admin)}

                sendNotificationEvent(idEvento, user, msg)
                return 'fatto'
            else:
                return 'solo ladmin puo modificare il nome di un evento'

        except Exception, e:
            sql.rollback()
            app.logger.error(str(e))
            return 'error'
        finally:
            cur.close()

    def delete(self, idEvento):
        user = session['idFacebook']
        print 'sono entrato in elimina'

        try:
            cur = sql.cursor()
            admin = Database.getAdminOfEvent(idEvento)

            if user == admin:
                print 'DEBUG: elimina evento'
                cur.execute("DELETE FROM party WHERE id_evento=%s", (idEvento,))
                msg = {'type': CODE.t['event'],
                       'method': CODE.m['del'],
                       'id_evento': str(idEvento),
                       'nome_evento': Database.getEventName(idEvento),
                       'admin_name': getFacebookName(admin)}

            else:
                print 'DEBUG: uscito evento'
                delUtenteFromEvent(idEvento, user)
                msg = {'type': CODE.t['event'],
                       'method': CODE.m['uscito'],
                       'id_evento': str(idEvento),
                       'nome_evento': Database.getEventName(idEvento),
                       'id_user': user,
                       'name_user': getFacebookName(user)}

            sendNotificationEvent(idEvento, user, msg)
            return 'fatto'

        except Exception, e:
            sql.rollback()
            print 'error ' + str(e)
            return 'error ' + str(e)
        finally:
            cur.close()

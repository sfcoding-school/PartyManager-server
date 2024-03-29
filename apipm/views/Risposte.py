import psycopg2
import psycopg2.extras
from flask import request
from flask import jsonify
from flask import session
from flask.views import MethodView
from flask import current_app as app

#HELPER#
from ..helper import *
#from ..helper.Database import sql


class Risposte(MethodView):

    def get(self, idEvento, idAttributo):
        # controllare che l evento e il mio
        #user = session['idFacebook']

        try:
            cur = sql.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""select risposte.id_risposta, risposta, id_user, template
                        from risposte natural join attributi left join rispose on risposte.id_risposta=rispose.id_risposta
                        where attributi.id_attributo=%s order by id_risposta""", (idAttributo,))

            sql.commit()
            risposte = cur.fetchall()

            ris = []
            if (len(risposte) != 0):
                ris.append({'id_risposta': risposte[0]['id_risposta'], 'risposta': risposte[0][
                           'risposta'], 'template': risposte[0]['template'], 'userList': []})

                for p in risposte:
                    if p['id_risposta'] != ris[len(ris) - 1]['id_risposta']:
                        ris.append({'id_risposta': p['id_risposta'], 'risposta': p[
                                   'risposta'], 'template': p['template'], 'userList': []})
                    if p['id_user'] is not None:
                        name = getFacebookName(p['id_user'])
                        ris[len(ris) -
                            1]['userList'].append({'id_user': p['id_user'], 'name': name})

        except Exception, e:
            sql.rollback()
            return 'error ' + str(e)
        finally:
            cur.close()

        return jsonify(results=ris)

    def post(self, idEvento, idAttributo):
        if request.form['risposta'] != '':
            risposta = request.form['risposta']
            user = session['idFacebook']

            try:
                cur = sql.cursor()
                #cur.execute("SELECT num_risposta FROM risposte WHERE id_attributo=%s and max=true",(idAttributo,))
                #numRispostaMax = cur.fetchone()[0]

                cur.execute(
                    "INSERT INTO risposte(risposta,id_attributo) VALUES(%s,%s) RETURNING id_risposta", (risposta, idAttributo))
                idRisposta = str(cur.fetchone()[0])
                #cur.execute("UPDATE attributi SET num_risposte = num_risposte + 1 WHERE id_attributo = %s",(idAttributo,))
                sql.commit()

                # if numRispostaMax <= 1:
                #    cambiaMaxRisposta()

                cur.execute(
                    "INSERT INTO rispose(id_risposta,id_attributo,id_user) VALUES(%s,%s,%s)", (idRisposta, idAttributo, user))
                sendNotificationEvent(idEvento, user, {'type': code.type.risposta,
                                                       'method': code.method.new,
                                                       code.risposta.agg: '0',
                                                       code.user.id: user,
                                                       code.evento.id: str(idEvento),
                                                       code.attributo.id: str(idAttributo),
                                                       code.risposta.id: str(idRisposta),
                                                       code.risposta.nome: risposta
                                                       })

            except Exception, e:
                if isinstance(e, psycopg2.Error):
                    sql.rollback()
                    # return str(e.diag.constraint_name)
                    print 'error SQL: ' + str(e)
                    if e.diag.constraint_name is not None and e.diag.constraint_name.find('rispose_pkey') != -1:
                        try:
                            cur.execute(
                                "UPDATE rispose SET id_risposta = %s WHERE id_user = %s and id_attributo = %s", (idRisposta, user, idAttributo))
                            sql.commit()

                            sendNotificationEvent(idEvento,
                                                  user,
                                                  {'type': code.type.risposta,
                                                   'method': code.method.new,
                                                   code.risposta.agg: '1',
                                                   code.user.id: user,
                                                   code.evento.id: str(idEvento),
                                                   code.attributo.id: str(idAttributo),
                                                   code.risposta.id: str(idRisposta),
                                                   code.risposta.nome: risposta
                                                   })
                        except Exception, e:
                            sql.rollback()
                            return 'error' + str(e)
                        return idRisposta
                return 'error' + str(e)
            finally:
                cur.close()

            return idRisposta
        else:
            return 'error POST paramaters'

    def put(self, idEvento, idAttributo, idRisposta):

        #idRisposta = request.form.get('idRisposta')
        risposta = request.form.get('risposta')
        user = session['idFacebook']

        if risposta is not None:
            return self.modificaDomandaChiusa(idEvento, idAttributo, idRisposta, risposta)

        try:
            cur = sql.cursor()
            #cur.execute("UPDATE attributi SET num_risposte = num_risposte + 1 WHERE id_attributo = %s",(idAttributo,))
            #cur.execute("UPDATE risposte SET num_risposta = num_risposta + 1 WHERE id_risposta = %s",(idRisposta,))
            # sql.commit()
            cur.execute(
                "INSERT INTO rispose(id_risposta,id_attributo,id_user) VALUES(%s,%s,%s)", (idRisposta, idAttributo, user))
            '''
            cur.execute("select domanda from attributi where id_attributo=%s", (idAttributo,))
            sql.commit()
            domanda = cur.fetchone()[0]
            '''
            cur.execute(
                "SELECT num_risposta FROM risposte where id_risposta=%s", (idRisposta,))
            sql.commit()
            risposta = cur.fetchone()

            sendNotificationEvent(idEvento, user, {'type': code.type.risposta,
                                                   'method': code.method.modify,
                                                   code.risposta.agg: '0',
                                                   code.user.id: user,
                                                   code.evento.id: str(idEvento),
                                                   code.attributo.id: str(idAttributo),
                                                   code.risposta.id: str(idRisposta),
                                                   code.risposta.num: str(risposta[0])})

        except Exception, e:
            if isinstance(e, psycopg2.Error):
                sql.rollback()
                # return str(e.diag.constraint_name)
                if e.diag.constraint_name.find('rispose_pkey') != -1:
                    try:
                        cur.execute(
                            "UPDATE rispose SET id_risposta = %s WHERE id_user = %s and id_attributo = %s", (idRisposta, user, idAttributo))
                        sql.commit()
                        '''
                        cur.execute(
                            "select domanda from attributi where id_attributo=%s", (idAttributo,))
                        sql.commit()
                        domanda = cur.fetchone()[0]
                        '''
                        cur.execute(
                            "SELECT num_risposta FROM risposte where id_risposta=%s", (idRisposta,))
                        sql.commit()
                        risposta = cur.fetchone()

                        sendNotificationEvent(idEvento, user, {'type': code.type.risposta,
                                                               'method': code.method.modify,
                                                               code.risposta.agg: '1',
                                                               code.user.id: user,
                                                               code.evento.id: str(idEvento),
                                                               code.attributo.id: str(idAttributo),
                                                               code.risposta.id: str(idRisposta),
                                                               code.risposta.num: str(risposta[0])})
                    except Exception, e:
                        sql.rollback()
                        return 'error' + str(e)
                    return 'aggiornato'
            return 'error' + str(e)
        finally:
            cur.close()

        return str(idRisposta)

    def modificaDomandaChiusa(self, idEvento, idAttributo, idRisposta, risposta):
        print 'entrato in modifica risposta'
        user = session['idFacebook']
        chiusa = Database.isAttributoChiuso(idAttributo)
        admin = Database.getAdminOfEvent(idEvento)

        if chiusa and user == admin:
            try:
                cur = sql.cursor()
                cur.execute("""UPDATE risposte
                               SET risposta=%s
                               WHERE id_risposta=%s""",
                            (risposta, idRisposta))
                sql.commit()

                sendNotificationEvent(idEvento, user, {'type': code.type.risposta,
                                                       'method': code.method.modify,
                                                       code.risposta.agg: '0',
                                                       code.user.id: user,
                                                       code.evento.id: str(idEvento),
                                                       code.attributo.id: str(idAttributo),
                                                       code.risposta.id: str(idRisposta)})
                return 'fatto'

            except Exception, e:
                sql.rollback()
                print 'error' + str(e)
                return 'error' + str(e)
        else:
            return 'non sei admin di questo evento'


    def delete(self, idEvento, idAttributo, idRisposta):
        user = session['idFacebook']
        print 'route: elimina RISPOSTA'

        try:
            admin = Database.getAdminOfEvent(idEvento)
            # verificare che la risposta fa parte di quell'evento

            if user == admin:
                cur = sql.cursor()
                cur.execute("DELETE FROM risposte WHERE id_risposta=%s", (idRisposta,))
                sql.commit()
                sendNotificationEvent(idEvento,
                                      user,
                                      {'type': code.type.risposta,
                                       'method': code.method.delete,
                                       code.user.id: user,
                                       code.evento.id: str(idEvento),
                                       code.user.idAdmin: admin,
                                       code.attributo.id: str(idAttributo),
                                       code.risposta.id: str(idRisposta)})
                return 'fatto'
            else:
                return 'error: solo l admin puo eliminare una domanda'

        except Exception, e:
            sql.rollback()
            return 'error ' + str(e)
        finally:
            cur.close()

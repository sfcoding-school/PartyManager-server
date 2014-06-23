import psycopg2, psycopg2.extras, collections

from flask import Flask
from flask import request
from flask import jsonify
from flask import session
from flask.views import MethodView

#HELPER#
from ..helper import *
#from ..helper.Database import sql

class Risposte(MethodView):
    def get(self,idEvento,idAttributo):
        #controllare che l evento e il mio
        
        user = session['idFacebook']
        
        try:
            cur = sql.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute("""select risposte.id_risposta, risposta, id_user, template 
                        from risposte natural join attributi left join rispose on risposte.id_risposta=rispose.id_risposta
                        where attributi.id_attributo=%s order by id_risposta""",(idAttributo,))
            
            sql.commit()
            risposte = cur.fetchall()
            
            ris = []
            if (len(risposte) != 0):
                ris.append({'id_risposta': risposte[0]['id_risposta'], 'risposta': risposte[0]['risposta'], 'template': risposte[0]['template'], 'userList': []})
            
                for p in risposte:
                    if p['id_risposta'] != ris[len(ris)-1]['id_risposta']:
                        ris.append({'id_risposta': p['id_risposta'], 'risposta': p['risposta'], 'template': p['template'], 'userList': []})
                    if p['id_user'] is not None:
                        name = getFacebookName(p['id_user'])
                        ris[len(ris)-1]['userList'].append({'id_user': p['id_user'], 'name': name})
                        
        except Exception, e:
            sql.rollback()
            return 'error ' + str(e)
        finally:
            cur.close()
        
        return jsonify(results = ris)

    def post(self,idEvento,idAttributo):
        if request.form['risposta']!='':
            
            #idAttributo = request.form['idAttributo']
            risposta = request.form['risposta']
            user = session['idFacebook']
            
            try:
                cur = sql.cursor()
                #cur.execute("SELECT num_risposta FROM risposte WHERE id_attributo=%s and max=true",(idAttributo,))
                #numRispostaMax = cur.fetchone()[0]
                
                cur.execute("INSERT INTO risposte(risposta,id_attributo) VALUES(%s,%s) RETURNING id_risposta",(risposta,idAttributo))
                idRisposta = str(cur.fetchone()[0])    
                #cur.execute("UPDATE attributi SET num_risposte = num_risposte + 1 WHERE id_attributo = %s",(idAttributo,))
                sql.commit()

                #if numRispostaMax <= 1:
                #    cambiaMaxRisposta()
                


                cur.execute("INSERT INTO rispose(id_risposta,id_attributo,id_user) VALUES(%s,%s,%s)",(idRisposta,idAttributo,user))

                cur.execute("select domanda from attributi where id_attributo=%s",(idAttributo,))
                domanda = cur.fetchone()[0]
                sql.commit()
                userName = getFacebookName(user)
                msg = {'type':'newRis', 'agg': '0', 'user': user, 'userName': userName, 'id_attributo': idAttributo, 'id_risposta': idRisposta, 'domanda': domanda, 'risposta': risposta}
                sendNotificationEvent(idEvento,user,msg)
                
            except Exception, e:
                if isinstance(e,psycopg2.Error):
                    sql.rollback()
                    #return str(e.diag.constraint_name)
                    print 'error SQL: ' + str(e)
                    if e.diag.constraint_name is not None and e.diag.constraint_name.find('rispose_pkey') !=-1:
                        try:
                            cur.execute("UPDATE rispose SET id_risposta = %s WHERE id_user = %s and id_attributo = %s", (idRisposta,user,idAttributo))
                            sql.commit()
                            
                            cur.execute("select domanda from attributi where id_attributo=%s",(idAttributo,))
                            domanda = cur.fetchone()[0]
                            sql.commit()
                            userName = getFacebookName(user)
                            msg = {'type':'newRis', 'agg': '1', 'user': user, 'userName': userName, 'id_attributo': idAttributo, 'id_risposta': idRisposta, 'domanda': domanda, 'risposta': risposta}
                            sendNotificationEvent(idEvento,user,msg)
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

    def put(self,idEvento,idAttributo):
        
        idRisposta = request.form['idRisposta']
        user = session['idFacebook']
        
        try:
            cur = sql.cursor()
            #cur.execute("UPDATE attributi SET num_risposte = num_risposte + 1 WHERE id_attributo = %s",(idAttributo,))
            #cur.execute("UPDATE risposte SET num_risposta = num_risposta + 1 WHERE id_risposta = %s",(idRisposta,))
            #sql.commit()

            cur.execute("INSERT INTO rispose(id_risposta,id_attributo,id_user) VALUES(%s,%s,%s)",(idRisposta,idAttributo,user))
            
            cur.execute("select domanda from attributi where id_attributo=%s",(idAttributo,))
            sql.commit()
            domanda = cur.fetchone()[0]
            cur.execute("select risposta, count(*) from rispose natural join risposte where id_risposta=%s group by risposta",(idRisposta,))
            sql.commit()
            risposta = cur.fetchone()[0]
            userName = getFacebookName(user)
            
            msg = {'type':'risp', 'agg':'0', 'user': user, 'userName': userName, 'id_attributo': idAttributo, 'id_risposta': idRisposta, 'domanda': domanda, 'risposta': str(risposta[0]), 'numr': str(risposta[1])}
            sendNotificationEvent(idEvento,user,msg)

        except Exception, e:
            if isinstance(e,psycopg2.Error):
                sql.rollback()
                #return str(e.diag.constraint_name)
                if e.diag.constraint_name.find('rispose_pkey') !=-1:
                    try:
                        ris = cur.execute("UPDATE rispose SET id_risposta = %s WHERE id_user = %s and id_attributo = %s",(idRisposta,user,idAttributo))
                        sql.commit()
                        
                        cur.execute("select domanda from attributi where id_attributo=%s",(idAttributo,))
                        sql.commit()
                        domanda = cur.fetchone()[0]
                        cur.execute("select risposta, count(*) from rispose natural join risposte where id_risposta=%s group by risposta",(idRisposta,))
                        sql.commit()
                        risposta = cur.fetchone()[0]
                        userName = getFacebookName(user)
                        
                        msg = {'type':'Risp', 'agg':'1', 'user': user, 'userName': userName, 'id_attributo': idAttributo, 'id_risposta': idRisposta, 'domanda': domanda, 'risposta': str(risposta[0]), 'numr': str(risposta[1])}
                        sendNotificationEvent(idEvento,user,msg)
                    except Exception, e:
                        sql.rollback()
                        return 'error' + str(e)
                    return 'aggiornato'
            return 'error' + str(e)
        finally:
            cur.close()

        return idRisposta

        '''
        try:
            cur = sql.cursor()
            cur.execute("INSERT INTO rispose(id_risposta,id_user) VALUES(%s,%s)",(idRisposta,user))
            sql.commit()

            cur.excute("SELECT id_attributo FROM risposte WHERE id_risposta=%s",(idRisposta,))
            sql.commit()
            idAttributo = cur.fetchone()[0]

            cur.execute("""SELECT num_utenti FROM party WHERE id_evento=
                            (SELECT id_evento FROM attributi WHERE id_attributo=%s""",(idAttributo,))
            sql.commit()
            numUtenti = cur.fetchone()[0]

            cur.execute("SELECT count(*) FROM rispose WHERE id_risposta=%s",(idRisposta,))
            sql.commit()
            countRis = cur.fetchone()[0]
            
            if numUtenti == countRis:
                cur.execute("SELECT risposta FROM risposte WHERE id_risposta=%s",(idRisposta,))
                cur.execute("""UPDATE attributi SET risposta = 
                                (SELECT risposta FROM risposte WHERE id_risposta=%s)
                                WHERE id_attributo = %s""",(idRisposta,idAttributo))

        except Exception, e:
            sql.rollback()
            return 'error '+str(e)
        finally:
            cur.close()

        return 'fatto'
        '''
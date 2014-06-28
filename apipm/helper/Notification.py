from gcm import GCM
from gcm.gcm import GCMNotRegisteredException
from gcm.gcm import GCMUnavailableException
gcmSender = GCM('AIzaSyDz0b7i-9n3UPTXXrySRcfK90UfKweweUc')

from flask import request
from flask import current_app as app

#HELPER#
from .Database import *
#from ..helper import sql

'''
CODE = {'newEvent': '1',
        'newAttr': '2',
        'newRis': '3',
        'risp': '4',
        'delEvent': '5',
        'uscitoEvent': '6',
        'delAttr': '7',
        'addFriends': '8',
        'delFriends': '9',
        'delRis': '10',
        'test': '11'
        }
'''


class CODE:
    t = {'event': '1',
         'attr': '2',
         'risp': '3',
         'user': '4',
         'test': '5'
         }

    m = {'new': '1',
         'mod': '2',
         'del': '3',
         'uscito': '4'
         }


def sendNotification(idFacebook, message):
    try:
        cur = sql.cursor()
        cur.execute("SELECT id_cell FROM utenti WHERE id_user=%s", (idFacebook,))
        sql.commit()
        idReg = str(cur.fetchone()[0])
    except Exception, e:
        sql.rollback()
        return 'error2' + str(e)
    finally:
        cur.close()

    try:
        canonical_id = gcmSender.plaintext_request(registration_id=idReg, data=message)

        if canonical_id:
            # Repace reg_id with canonical_id in your database
            try:
                cur = sql.cursor()
                cur.execute(
                    "UPDATE utenti SET id_cell = %s WHERE id_cell = %s", (canonical_id, idReg))
                sql.commit()
            except Exception, e:
                sql.rollback()
                return 'error3 ' + str(e)
            finally:
                cur.close()

        return None

    except GCMNotRegisteredException:
        # Remove this reg_id from database
        return 'error: reg_id non presente'
    except GCMUnavailableException:
        return 'error: altra roba'
    except Exception, e:
        return str(e)


def sendNotificationEvent(idEvento, user, message):
    try:
        cur = sql.cursor()
        debug = request.args.get('debug') if request.args.get('debug') is not None else 'false'
        print 'SEND NOTIFICATION: ' + debug
        if debug == 'true':
            cur.execute(
                "select array(select id_cell from evento natural join utenti where id_evento=%s)", (idEvento,))
        else:
            cur.execute("""SELECT array(SELECT id_cell
                                        FROM evento NATURAL JOIN utenti
                                        WHERE id_evento=%s and id_user<>%s)""",
                        (idEvento, user))
        sql.commit()
        regIds = cur.fetchall()[0][0]
        #print 'regIds: ' + str(regIds)
        response = gcmSender.json_request(registration_ids=regIds, data=message)

        # Handling errors
        if 'errors' in response:
            print 'error GCM: send notification'
            # for error, reg_ids in response['errors'].items():
                # Check for errors and act accordingly
                # if error is 'NotRegistered':
                    # Remove reg_ids from database
                    # for reg_id in reg_ids:

        if 'canonical' in response:
            print 'canonical change'
            for reg_id, canonical_id in response['canonical'].items():
                # Repace reg_id with canonical_id in your database
                cur.execute(
                    "UPDATE utenti SET id_cell = %s WHERE id_cell = %s", (canonical_id, reg_id))
                sql.commit()

    except Exception, e:
        sql.rollback()
        print 'error GCM: ' + str(e)
    finally:
        cur.close()

import httplib
import socket
import couchdb
import getcreds as cr
import thelogger as l
import time

class CouchDBConn(object):
    def __init__(self):
        self.couch = None
        self.logger = l.get_logger(__name__) 

    def getServerInstance(self,server_url,credential_file):
        '''Given a couchDB server url and a file with credentials parsed by
        the credentials library, initializes the server instance used by 
        other class methods to get database data'''
        #Connection info for couchdb
        couch = couchdb.Server(server_url)
        couchuser, couchpassword = cr.getcreds(credential_file)
        couch.resource.credentials = (couchuser, couchpassword)
        couch.resource.session.timeout = 15
        self.couch = couch
	self.logger.info("CouchDBConn: Got server instance successfully.")

    def _connectToDB(self,dbName):
        '''Given the database name for the connected server, returns the
        status of the connection and the database instance itself.  This
        is generally used by other methods written to save/update the
        database instance'''
        status = "ok"
        db = {}
        numtries = 0
        while numtries < 3:
            try:
               db = self.couch[dbName]
               break
            except socket.error, exc:
                print "Failed to connect to " + dbName
                self.logger.exception("Failed to connect to " + dbName)
                numtries += 1
                self.logger.info("At try " + str(numtries) + ". Trying again..")
                time.sleep(1)
                status = "bad"
                continue
            except httplib.INTERNAL_SERVER_ERROR:
                print "Failed to connect to " + dbName
                self.logger.exception("Server error: Failed to connect to " + dbName)
                numtries += 1
                self.logger.info("At try " + str(numtries) + ". Trying again..")
                time.sleep(1)
                status = "bad"
                continue
        return status, db

    def getLatestEntry(self,dbname,viewname,dbdict_last=None):
        '''Given the name of the database on the server and the couch view, and
        the previous channel database dictionary, returns the most current
        channel database dictionary.  If connection fails, returns the same
        channeldb as was given, or an empty dict if dbdict_last is None.'''
        dbdict = {}                                                                                    
        counter = 0
        dbParStatus, dbPar = self._connectToDB(dbname)                                       
        if dbParStatus is "ok":
            while counter < 3:                                                                         
                try:
                    queryresults =  dbPar.view(viewname,descending=True,limit=1)                    
                    dbdict = queryresults.rows[0].value
                    break
                except socket.error, exc:
                    self.logger.exception("Failed to view database %s, view %s. "%(dbname,viewname) + \
                        "sleeping, trying again... ERR: " + str(exc))
                    time.sleep(1)
                    counter += 1
                    dbParStatus, dbPar = self._connectToDB(dbname)
                    continue
        else:
            self.logger.exception("IN getChannelParameters: could not connect" + \
                " to %s. returning last dict."%(dbname))
            if dbdict_last is None:
                dbdict = {}
            else:
                dbdict = dbdict_last
        return dbdict

  

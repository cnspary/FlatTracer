import os
import logging
import wget

from EnvVariables import UnifiedLog

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%m/%d/%Y %H:%M:%S %p"
logging.basicConfig(filename=UnifiedLog, level=logging.INFO, format=LOG_FORMAT, datefmt=DATE_FORMAT)

from EnvVariables import GAV2AVForm
from EnvVariables import timeout

class DownloadJar:

    # get maven center repo url
    def GAV2UrlForm(self, origin_name):
        string = origin_name
        parts = string.split(':')
        parts[0] = parts[0].replace('.', '/')
        url = '/'.join(parts[:2]) + '/' + parts[2] + '/'
        return url

    # get local download path
    def GAV2DownloadPath(self, origin_name):
        path = 'https://repo.maven.apache.org/maven2/' + self.GAV2UrlForm(origin_name) + GAV2AVForm(origin_name) + ".jar"
        return path

    def run(self, chain, DownloadRoot):
        #logging.info("Chain to Download = %s", chain)
        for j in range(0, len(chain)):
            package = chain[j]

            possibleFilePos = DownloadRoot + GAV2AVForm(package) + ".jar" 
            if os.path.isfile(possibleFilePos):
                print("GAV = " + package + " Download Already " + "into " + possibleFilePos)
                #logging.info("GAV = " + package + " Download Already " + "into " + possibleFilePos)
            else:
                try:
                    self.doDownload(self.GAV2DownloadPath(package), DownloadRoot)
                    #logging.info("GAV = " + package + " Download Success "  + "into " + possibleFilePos)
                except TimeoutError:
                    #logging.error("GAV = " + package + " TIME OUT STEP 1 for " + self.GAV2DownloadPath(package))
                    return 1
                except Exception as e:
                    #logging.error("GAV = " + package + " Download Exception " + str(e) + " for" + self.GAV2DownloadPath(package))
                    return 1
            return 0

    @timeout(300)
    def doDownload(self, url, storeAddress):
        wget.download(url, storeAddress)
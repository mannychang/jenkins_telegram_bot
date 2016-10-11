import sys

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater

import config
import jenkins
import strings

reload(sys)
sys.setdefaultencoding('utf-8')

# jenkins server instance
server = None
# record jenkins job list
jobs = []


def init(url, username, token):
    global server
    server = jenkins.Jenkins(url, username, token)
    user = server.get_whoami()
    print '[Jenkins bot] loggined url: %s, user: %s' % (url, user['id'])

    global jobs
    jobs = server.get_jobs()


def refresh():
    init()


def isAllowedUsers(username):
    if username in config.allowed_users:
        return True
    else:
        return False


def isValidJobName(jobName):
    for job in jobs:
        if job['fullname'] == jobName:
            return True
    print strings.INVALID_JOB_NAME
    return False


def listJobs():
    running_builds = server.get_running_builds()
    for job in jobs:
        state = 'idle'
        for r in running_builds:
            if r['name'] == job['fullname']:
                state = 'running#%d' % r['number']
        print '%s: %s' % (job['fullname'], state)


def startBuildJob(jobName):
    if not isValidJobName(jobName):
        return False, strings.INVALID_JOB_NAME

    if not isAlreadyBuilding(jobName):
        print 'building ' + jobName
        server.build_job(jobName)
        return True, 'building ' + jobName
    else:
        print jobName + string.ALREADY_BUILD
        return False, jobName + string.ALREADY_BUILD


def isAlreadyBuilding(jobName):
    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            return True
    return False


def stopBuildJob(jobName):
    if not isValidJobName(jobName):
        return False, strings.INVALID_JOB_NAME

    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            print 'stop %s#%d, %s' % (r['name'], r['number'], r['url'])
            server.stop_build(jobName, r['number'])
            return True, 'stop %s#%d, %s' % (r['name'], r['number'], r['url'])

    print jobName + strings.NO_JOB_BUILDING
    return False, jobName + strings.NO_JOB_BUILDING


if __name__ == '__main__':
    init(config.jenkins_url, config.jenkins_username, config.jenkins_token)
    listJobs()

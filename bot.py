import sys

from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async

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


def isAllowedUsers(bot, update):
    username = update.message.from_user.username
    if username in config.allowed_users:
        return True
    else:
        s = 'Invalid User: ' + ' [' + username + ']'
        bot.sendMessage(update.message.chat_id, text=s)
        return False


def isValidJobName(jobName):
    for job in jobs:
        if job['fullname'] == jobName:
            return True
    print strings.INVALID_JOB_NAME
    return False


@run_async
def listJobs(bot, update):
    if not isAllowedUsers(bot, update):
        return
    s = 'job list'

    running_builds = server.get_running_builds()
    for job in jobs:
        state = 'idle'
        for r in running_builds:
            if r['name'] == job['fullname']:
                state = 'running#%d' % r['number']
        s = '\n'.join([s, '%s: %s' % (job['fullname'], state)])

    print s
    bot.sendMessage(update.message.chat_id, text=s)


@run_async
def startBuildJob(bot, update, args):
    if not isAllowedUsers(bot, update):
        return
    if args:
        jobName = args[0]
    else:
        jobName = ''

    if not isValidJobName(jobName):
        bot.sendMessage(update.message.chat_id, text=strings.INVALID_JOB_NAME)
        return

    if not isAlreadyBuilding(jobName):
        print 'building ' + jobName
        server.build_job(jobName)
        s = 'start building ' + jobName
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return
    else:
        s = jobName + string.ALREADY_BUILD
        print s
        bot.sendMessage(update.message.chat_id, text=s)
        return


def isAlreadyBuilding(jobName):
    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            return True
    return False


@run_async
def stopBuildJob(bot, update, args):
    if not isAllowedUsers(bot, update):
        return
    if args:
        jobName = args[0]
    else:
        jobName = ''

    if not isValidJobName(jobName):
        bot.sendMessage(update.message.chat_id, text=strings.INVALID_JOB_NAME)
        return

    running_builds = server.get_running_builds()
    for r in running_builds:
        if r['name'] == jobName:
            s = 'stop %s#%d, %s' % (r['name'], r['number'], r['url'])
            print s
            server.stop_build(jobName, r['number'])
            bot.sendMessage(update.message.chat_id, text=s)
            return

    s = jobName + strings.NO_JOB_BUILDING
    print s
    bot.sendMessage(update.message.chat_id, text=s)


def error(bot, update, error):
    print 'Update "%s" caused error "%s"' % (update, error)


def help(bot, update):
    s = '\n'.join(
            ['/help # get help', '/list #list all jobs',
                '/build jobName # start build jobName',
                '/stop jobName # stop build jobName'])
    bot.sendMessage(update.message.chat_id, text=s)


def main():
    # init jenkins
    init(config.jenkins_url, config.jenkins_username, config.jenkins_token)
    # Create the EventHandler and pass it your bot's token
    updater = Updater(config.telegram_bot_token)
    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # add command handlers
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", listJobs))
    dp.add_handler(CommandHandler("build", startBuildJob, pass_args=True))
    dp.add_handler(CommandHandler("stop", stopBuildJob, pass_args=True))

    # log all errors
    dp.add_error_handler(error)

    # start bot
    updater.start_polling()

    # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()

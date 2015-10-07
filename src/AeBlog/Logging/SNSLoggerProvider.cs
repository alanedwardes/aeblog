﻿using AeBlog.Clients;
using AeBlog.Options;
using Amazon.SimpleNotificationService;
using Microsoft.Framework.Logging;
using Microsoft.Framework.OptionsModel;

namespace AeBlog.Logging
{
    public class SNSLoggerProvider : ISNSLoggerProvider
    {
        private readonly IOptions<General> general;
        private readonly IAmazonSimpleNotificationService client;

        public SNSLoggerProvider(ISNSClientFactory factory, IOptions<General> general)
        {
            client = factory.CreateSimpleNotificationClient();
            this.general = general;
        }

        public ILogger CreateLogger(string name)
        {
            return new SNSLogger(client, name, general.Options.SnsErrorsTopic);
        }

        public void Dispose()
        {
            client.Dispose();
        }
    }
}
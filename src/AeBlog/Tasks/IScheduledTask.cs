﻿using System;
using System.Threading;
using System.Threading.Tasks;

namespace AeBlog.Tasks
{
    public interface IScheduledTask : ITask
    {
        TimeSpan Schedule { get; }
    }
}

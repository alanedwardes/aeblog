﻿namespace AeBlog.Models
{
    public class Post : PostSummary
    {
        public string Content { get; set; }
        public bool IsSingle { get; set; }
    }
}
﻿using System;

namespace AeBlog.Models
{
    public class PostSummary
    {
        public string Slug { get; set; }
        public string Category { get; set; }
        public DateTime Published { get; set; }
        public string Title { get; set; }
        public string Type { get; set; }
        public string Content { get; set; }
        public bool HasMore { get; set; }
    }
}
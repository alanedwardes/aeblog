﻿namespace AeBlog.Display
{
    public class LayoutParameters
    {
        public LayoutParameters(string title, ViewType viewType)
        {
            Title = title;
            ViewType = viewType;
        }

        private string title;

        public string Title { get; }

        public ViewType ViewType { get; }

        public string Theme => ThemePicker.PickRandomTheme();
    }
}
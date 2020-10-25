using AeBlog.Services;
using Amazon;
using Amazon.DynamoDBv2;
using Google.Apis.Services;
using Google.Apis.YouTube.v3;
using Microsoft.AspNetCore.Authentication.Cookies;
using Microsoft.AspNetCore.Authentication.Twitter;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using System.IO;
using System.Net.Http;

namespace AeBlog
{
    public class Startup
    {
        public void ConfigureServices(IServiceCollection services)
        {
            services.AddMvc();
            services.AddSingleton<IImageRepository, ImageRepository>();
            services.AddSingleton<IColourRepository, ColourRepository>();
            services.AddSingleton<IBlogPostRepository, BlogPostRepository>();
            services.AddSingleton<IAmazonDynamoDB>(new AmazonDynamoDBClient(RegionEndpoint.EUWest1));

            var configuration = new ConfigurationBuilder()
                .AddEnvironmentVariables()
                .AddJsonFile(Path.Combine(Directory.GetCurrentDirectory(), "config.json"), true)
                .AddJsonFile(Path.Combine(Directory.GetCurrentDirectory(), "config.secret.json"), true)
                .Build();

            services.AddSingleton<IConfiguration>(configuration);
            services.AddSingleton(new HttpClient());

            services.AddSingleton(new YouTubeService(new BaseClientService.Initializer()
            {
                ApiKey = configuration["YOUTUBE_API_KEY"],
                ApplicationName = "aeblog"
            }));

            services.AddAuthentication(CookieAuthenticationDefaults.AuthenticationScheme)
                    .AddCookie(options =>
                    {
                        options.LoginPath = "/admin/login";
                        options.AccessDeniedPath = "/admin/denied";
                    })
                    .AddTwitter(options =>
                    {
                        options.CallbackPath = "/admin/auth/twitter-signin";
                        options.ConsumerKey = configuration["TWITTER_CONSUMER_KEY"];
                        options.ConsumerSecret = configuration["TWITTER_CONSUMER_SECRET"];
                    });

            services.AddRouting(options => options.AppendTrailingSlash = true);

            services.AddAuthorization(options =>
            {
                var isAdminPolicy = new AuthorizationPolicyBuilder(new[] { TwitterDefaults.AuthenticationScheme })
                    .RequireClaim("urn:twitter:userid", "14201790")
                    .Build();

                options.AddPolicy("IsAdmin", isAdminPolicy);
            });

            services.AddMemoryCache();

            services.AddDataProtection()
                    .PersistKeysToAWSSystemsManager("/aeblog/dataprotection");
        }

        public void Configure(IApplicationBuilder app, ILoggerFactory loggerFactory, IWebHostEnvironment environment)
        {
            app.UseExceptionHandler("/error");

            loggerFactory.AddLambdaLogger();

            app.UseStaticFiles();
            app.UseStatusCodePagesWithReExecute("/error");

            app.UseRouting();

            if (!environment.IsDevelopment())
            {
                app.UseAuthentication();
                app.UseAuthorization();
            }

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
                endpoints.MapDefaultControllerRoute();
            });
        }
    }
}

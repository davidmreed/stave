# Building Events and Forms

Stave gives you a lot of freedom to create, share, and staff your events your way. See the [Key Concepts](./key_concepts.md) section to learn more about the relationship between Events, Games, and Application Forms.

## Creating an Event

Start by visiting your league page by

Click Create Event. Stave offers you a choice of _Event Templates_. Event Templates are part of your [league's setup](./league_management.md). Most leagues will have a set of Event Templates provided by Stave, which include

- Singleheader
- Doubleheader
- Tournament

You can choose a template that sounds like what your Event needs, even if it's not exactly right, because you'll be able to change all of the setup once the Event is created. Alternately, you can choose not to use an Event Template and set everything up yourself.

Enter the data on your Event. It's up to you whether or not to enter Game information. If you already known your Game schedule (times, game types, perhaps even teams), you can go ahead and add Games to your Event. It's fine, however, to add that information later.

Select the Role Groups that you plan to staff for this Event. You'll be able to add Application Forms for the Role Groups you choose later.

Stave lets you take as much time as you need to draft your Event. Notice that it starts in the _Drafting_ status, which means that nobody can see it unless they're an Event Manager for your League. When you're ready to show the Event to other users, you can update the Status to _Open_, which lets anyone on Stave see it, or _Link Only_, which lets anyone with the link see the Event but does not include it in Stave's listings. Stave shows you a banner when your Event is still Drafting so that you don't send the link to anyone else.

An Event by itself can hold a slot on a [calendar](./calendars.md), helping users plan their participation. Add an Application Form to let users to apply to participate.

## Building an Application Form

If you started your Event from an Event Template, it might already have Application Forms associated with it; some templates come with forms. You can add a new Application Form by clicking the Create button on the Event detail page, or edit an existing one by clicking Edit beside its name.

> [!NOTE]
> You can only have one Application Form for each Role Group.

When you create an Application Form, you'll set a few important fields that control how your form works, and then add all of the information you want to gather from your applicants.

### Core Configuration

You can choose a _slug_, which will appear in the link for your form. Generally, Stave recommends using `apply` as the slug for a single Application Form on an Event, or `apply-nso-so` (adding the Role Group names) for multiple Application Forms on an Event. The slug has to be unique within the scope of an Event.

Pick which Role Groups you plan to staff with this Application Form. You can choose any combination of Role Groups that are configured on the Event. Remember that you can have more than one Application Form! A good rule of thumb is that if you make staffing decisions about Role Groups as part of _one_ process (like skating and nonskating officials), they should be on a single Application Form. If you don't, or if you need to ask for different information from applicants to different Role Groups, they should probably be on separate Application Forms.

Stave offers two _application processes_, which you can choose for each Application Form independently.

- Assign Only. This process is typically used by smaller events. Applicants receive a schedule email when they are staffed. There is no invitation or confirmation process.
- Confirm then Assign. This process is typically used by larger events and tournaments. Applicants are sent an invitation email when they are accepted and are asked to confirm or decline their participation. If they confirm, they receive a schedule email when they are staffed.

Application Forms can use one of three _availability types_ to ask applicants what portions of the Event they can work:

- Entire Event. With this model, applicants are assumed to be available for the whole Event, whether it's two hours or two days.
- By Day. This model is for multi-day Events. Applicants select which day or days they are available, and can be staffed at any time on those days.
- By Game. This model is for multi-Game Events. Applicants select which Games they are available and can only be staffed for those Games, regardless of how many total Games or days are in the Event.

You can choose your availability model separately for each Application Form. Single-Game Events can only use the Entire Event model. One-day Events cannot use the By Day model.

Your form can present _intro text_ to the user before they're asked questions. This is your opportunity to describe the process, the event, or offer whatever other messaging you need. You can write text formatted with [Markdown](https://en.wikipedia.org/wiki/Markdown) in this field, which allows you to use bold (`**like this**`), italic (`_like this_`), and links (`[link text goes here](https://stave.app/your-link-goes-here/)`). [Learn to use Markdown in 60 seconds](https://commonmark.org/help/).

When Stave sends messages to applicants (covered in detail in [Staffing](./staffing.md)), it uses _Message Templates_ to create those messages. Message Templates let you use a standard email message, but substitute in key information like the user's name, the event dates, and more. They're configured in your [League Management](./league_management.md).

Here, you'll choose an email template for sending invitations, rejections, and assignments. You can leave these blank if you wish; you can write messages when you need to send them. In most cases, you'll want to leave the default or the value chosen by your Application Form Template in place.

> [!NOTE]
> Stave _never_ sends status emails to applicants until you explicitly ask it to do so. Applicants receive an acknowledgement of their application automatically. After that, you're in control of outreach. See [Staffing](./staffing.md) for more.

### Application Data

All Application Forms have four main sections:

1. Profile Information
1. Availability
1. Roles
1. Custom Questions

Stave stores common information on each user's profile, so that they need not retype it for each application they submit. The Stave profile includes information like the derby name, legal name, certification status, and game history link. You can choose which profile fields you'd like to receive for this Application Form.

> [!NOTE]
> You cannot change your selected profile fields after you receive your first application.

You can add any number of custom Questions to your Application Form. Questions can be

- Short Text, which accepts a single line (up to 10KB of text).
- Long Text, which accepts a paragraph (up to 10KB of text).
- Choose One, which accepts a single selection from choices you provide. (You can use a Choose One question with the options Yes and No!)
- Choose Multiple, which accepts any number of selections from choices you provide. You can also choose to offer an Other option, which the user can answer with free text.

When you staff based on your applications, you'll be able to see answers to your custom questions alongside the other data provided by the applicant.

> [!NOTE]
> You cannot add or remove your custom Questions after you receive your first application, and you cannot change choices on Choose One or Choose Multiple questions. You can change the text of question titles any time.


## Next Steps

Time to start [staffing](./staffing.md)! You can share your Application Form link wherever you typically promote your events. Keep in mind that your Event needs to be in Link Only or Open status for your forms to be visible to other users.

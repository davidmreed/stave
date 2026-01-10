# League Management

Stave works out of the box for most roller derby leagues. However, spending some time configuring your league can save you a lot of time over the course of a season. Stave's templating features let you save common event layouts, application form designs, and messages so that you can reuse them over and over. And you can customize the roles for which you staff to match your league's officiating style, or to bring in other volunteers like announcers or photographers.

## Permissions

Stave users can have two levels of permission to work with a league.

League Manager
: A league manager can change all aspects of the league's configuration, including templates, Roles and Role Groups, and the permissions of other users.

Event Manager
: An event manager can create, configure, and staff events, but cannot change league configuration.

The user who creates a league is both an Event Manager and a League Manager. To add permissions to other users, [contact Stacktrace](mailto:david@ktema.org).

> [!NOTE]
> A self-service permissions management feature is coming soon.

## Roles and Role Groups

Stave Events are staffed based on [Roles and Role Groups](./key-concepts.md#roles-and-role-groups). Out of the box, Stave has Role Groups for NSO (Non-Skating Official), SO (Skating Official), and THO (Tournament Head Official) Roles, using common staffing layouts used by many roller derby leagues. Your league might have different needs, or larger goals. Perhaps you have a large enough community to staff a dedicated PW (Penalty Wrangler). Or you might want to offer signup forms not just for officials, but also for announcers, photographers, or medics. You can customize your Roles and Role Groups to suit those needs.

### Role Group Terminology

Event-Only
: An Event-Only Role Group is used to staff Roles that span a whole Event, not a specific Game or time span. For example, Tournament Head Officials are Event-Only Roles.

Nonexclusive
: Most Roles require the full attention of a crew member. Some, however, can coexist. When a Role is marked Nonexclusive, it can be held at the same time as another Role from the same Role Group. The HNSO Role is Nonexclusive.

### Customizing Existing Roles and Role Groups

> [!CAUTION]
> You cannot delete Roles or Role Groups that are in use on Events or Application Forms.

To customize your existing Roles and Role Groups, including the out-of-the-box Role Groups,

1. Find your league in the My Leagues section on the homepage.
1. Click the Roles link.
1. Locate the Role Group you'd like to update. Stave will tell you if it cannot be deleted due to existing uses.
1. Click Edit.
1. Make changes to the Role Group's name and description or those of the Roles. You can also add new Roles by clicking Add Role to Role Group, even if the Role Group is in use.
1. Click Save.

### Adding New Role Groups

> [!NOTE]
> Role Groups need to be selected on an Event or Application Form (or their templates) before it can be used.

To add a new Role Group,

1. Find your league in the My Leagues section on the homepage.
1. Click the Roles link.
1. Click the Create button in the header.
1. Enter a name for the Role Group.
1. Add at least one Role by clicking Add Role to Role Group.
1. Click Save.

## Event Templates

Most Events aren't unique. Leagues often run single games, doubleheaders, and other events whose structures look very similar. Event Templates make it easy to create Events from standardized patterns so that leagues can fill out seasons quickly and consistently.

Stave ships with three out-of-the-box Event Templates:

Singleheader
: A single-game, single-day event, with an attached Application Form that uses the Assign Only process.

Doubleheader
: A two-game, single-day event, with an attached Application Form that uses the Assign Only process.

Tournament
: A five-game, two-day event (you can change the game and day count!), with an attached Application Form that uses the Confirm, then Assign process.

Event Templates look very much like Events. This isn't accidental! If you're comfortable [building Events](./build-events-and-forms.md), Event Templates will look very familiar.

The most important difference is that Event Templates do not have dates. Instead, Event Templates have a count of Days. When you clone the Event Template to create an Event, Stave asks for the start date, and uses the Day count of the Event Template to find the end date. For example, if you clone an Event Template that's set to 2 days, and specify the start date as January 13, 2028, Stave will automatically set the end date of that Event to January 14, 2028. Likewise, Game Templates specify a day (from 1 to the number of days in the Event Template), and a start and end time. When you create an Event from the Template, Stave automatically places the Games on the right days and times.

You can also leave fields blank on an Event Template that would be required on an Event, including the Location field and most of the Game information. When you create an Event from the Template, you'll complete any fields left blank.

## Application Form Templates

Application Form Templates are nearly identical to [Application Forms](./build-events-and-forms.md). The key difference is how Application Form Templates are used with Event Templates. When you build an Event Template, you select zero or more Application Form Templates to associate with it. Application Form Templates can be used with multiple Event Templates. When an Event is created from an Event Template, each associated Application Form Template is used to create an Application Form for that Event.

Application Form Templates are an easy way to use a consistent set of questions on your Application Forms. You can build Application Form Templates for any combination of Role Groups and re-use them across Events so that your applicants and staffers see a standard set of application data.

## Message Templates

Message Templates can be attached to both Application Form Templates and Application Forms. Because Message Templates can use merge fields to substitute in Event information, they can be re-used across a variety of different Application Forms and Events.

Stave comes with three out-of-the-box Message Templates, one each for invitation emails, rejection emails, and assignment emails. You can edit the text of the default Message Templates, and your changes will apply across the built-in Event and Application Form Templates. You can also create your own Message Templates.

To learn about writing Message Templates and how to use merge fields, see [Messaging](./messaging.md).

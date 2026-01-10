# Messaging

Stave uses a simple, Markdown-based format with merge fields for messaging. Messaging is used in [Comm Center](./staffing.md#sending-communications) and supported by [Message Templates](./league-management.md#message-templates).

Messages and Message Templates are written in [Markdown](https://en.wikipedia.org/wiki/Markdown), which allows you to use bold (`**like this**`), italic (`_like this_`), and links (`[link text goes here](https://stave.app/your-link-goes-here/)`). [Learn to use Markdown in 60 seconds](https://commonmark.org/help/). Stave automatically renders your Markdown-formatted message into both an HTML email and a plain-text email when it's sent.

You can use _merge fields_ in your messages. Merge fields allow you to substitute in data from the Event, Application Form, Application, the applicant's profile, and your own profile. By using merge fields, you can make your Message Templates reusable across many different Events. Merge fields are supported in both the message's Subject and its Content.

Here's an example. The out-of-the-box Invitation Email template has the subject

```markdown
Invitation to officiate {event.name}
```

When an email is sent based on this template, Stave substitutes the Event's Name field for `{event.name}`.

and the content

```
Dear {user.preferred_name},

You're invited to officiate [{event.name}]({event.link}), hosted by {league.name}!

{event.name} takes place {event.date_range} at

{event.location}

To accept or decline your invitation, [click here]({application.link}). If you confirm, you'll receive another email when your assignments are finalized.

Thank you!

{sender.preferred_name} and {event.name} organizers
```

Likewise, when an email is sent based on this template, Stave substitutes in information from the user to whom it is being sent, the event, the league, the application, and the sender.

This email includes a link. The value of merge fields like `{event.link}` is a URL. Stave renders Markdown links like `[{event.name}]({event.link})` as a hyperlink with the Event's name as the title and the event's direct link as the target.

Every message editor on Stave includes a list of merge fields. Click the _Merge fields_ header to show all of the information you can include in your messages.

## Invitation Emails

Make sure to include the merge field `{application.link}`. The user can confirm or decline their invitation at this link.

## Assignment Emails

Make sure to include the merge field `{app_form.schedule_link}`. The user can view their assignments and schedule at this link.

# Ad-Hoc Flow

- User builds crews in Crew Builder. Crew Builder can use anyone not declined.
- Applications view used only to decline
- Communication tab shows who needs to receive emails, w/clickthrough to send.
- Anyone on the crew is on the invitation list.

# Tournament Flow

- User builds crews in Crew Builder. Crew Builder can use anyone not declined.
- Applications view used to decline or mark for invitation.
- Anyone on the crew OR marked for invitation is on the invitation list. (??)


```mermaid

flowchart LR
// Tournament flow
APPLIED --> INVITATION_PENDING --> INVITED --> CONFIRMED --> ASSIGNMENT_PENDING --> ASSIGNED
APPLIED --> INVITATION_PENDING --> INVITED --> DECLINED

// Ad-hoc flow
APPLIED --> ASSIGNMENT_PENDING --> ASSIGNED

// Both flows
APPLIED --> REJECTION_PENDING --> REJECTED
ANY_STATE --> WITHDRAWN

```


BUGS

- Test User Visible Status
- Review all required statuses for application form s- are we enforcing correctly?
- 500s when I hit Send Email with no template configured
- Add Schedule to the Staffing Header

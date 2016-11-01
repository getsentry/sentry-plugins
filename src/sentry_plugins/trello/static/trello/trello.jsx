import React from 'react';
import {plugins} from 'sentry';

class Trello extends plugins.DefaultIssuePlugin {
}

Trello.displayName = 'Suck it Trello';

plugins.add('trello', Trello);

export default Trello;

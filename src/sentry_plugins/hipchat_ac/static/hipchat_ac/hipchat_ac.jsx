import React from 'react';
import {plugins} from 'sentry';

import Settings from './components/settings';

class Hipchat extends plugins.BasePlugin {
    renderSettings(props) {
        return <Settings plugin={this} {...props} />;
    }
}

plugins.add('hipchat-ac', Hipchat);

export default Hipchat;

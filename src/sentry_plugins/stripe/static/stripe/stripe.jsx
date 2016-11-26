import React from 'react';
import {plugins} from 'sentry';

class StripeContext extends plugins.BaseContext {
    render() {
        return <div>hello</div>;
    }
}

plugins.addContext('default', StripeContext);

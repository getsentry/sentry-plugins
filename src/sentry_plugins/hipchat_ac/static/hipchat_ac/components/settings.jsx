import React from 'react';
import {i18n, IndicatorStore, LoadingError, LoadingIndicator, plugins} from 'sentry';

class Settings extends plugins.BasePlugin.DefaultSettings {
  constructor(props) {
    super(props);

    this.onTest = this.onTest.bind(this);
    this.fetchData = this.fetchData.bind(this);

    Object.assign(this.state, {
      tenants: null,
      tenantsLoading: true,
      tenantsError: false,
    });
  }

  fetchData() {
    super.fetchData();

    this.api.request(`${this.getPluginEndpoint()}tenants/`, {
      success: (data) => {
        this.setState({
          tenants: data,
          tenantsLoading: false,
          tenantsError: false,
        });
      },
      error: (error) => {
        this.setState({
          tenantsLoading: false,
          tenantsError: true,
        });
      }
    });
  }

  // TODO(dcramer): move this to Sentry core
  onTest() {
    let loadingIndicator = IndicatorStore.add(i18n.t('Saving changes..'));
    this.api.request(`${this.getPluginEndpoint()}test-config/`, {
      method: 'POST',
      success: (data) => {
        this.setState({
          testResults: data,
        });
      },
      error: (error) => {
        this.setState({
          testResults: {
            error: true,
            message: 'An unknown error occurred while testing this integration.',
          },
        });
      },
      complete: () => {
        IndicatorStore.remove(loadingIndicator);
      }
    });
  }
  renderLink(url, metadata) {
    let tenants = this.state.tenants;
    if (!tenants || !tenants.length) {
      if (metadata.onPremise) {
        return (
          <div>
            <p>
              Installing this integration will allow you to receive notifications
              for and assign team members to new Sentry errors within HipChat rooms.
              To install the integration, click the button below.
            </p>
            <p>
              <a href={url}
                 className="btn btn-primary"
                 target="_blank">Enable Integration</a>
            </p>
          </div>
        );
      } else {
        return (
          <div>
            <p>
              To add the Sentry integration to
              HipChat click on "Install an integration from a descriptor URL"
              on your room in HipChat and add the following descriptor URL:
            </p>
            <pre>{metadata.descriptor}</pre>
          </div>
        );
      }
    }
  }

  renderTenants(url) {
    let tenants = this.state.tenants;
    if (this.state.tenantsLoading)
      return <LoadingIndicator />;
    else if (this.state.tenantsError)
      return <LoadingError onRetry={this.fetchData} />;
    if (!tenants.length)
      return null;

    let isTestable = this.props.plugin.isTestable;
    return (
      <div>
      <h4>Active Rooms</h4>
        <table className="table" style={{fontSize: 14}}>
          <thead>
            <tr>
              <th>Room</th>
              <th>By</th>
              {isTestable &&
                <th>Test</th>
              }
            </tr>
          </thead>
          <tbody>
            {tenants.map((tenant) => {
              return (
                <tr key={tenant.id}>
                  <td>
                    <strong>{tenant.room.name}</strong><br />
                    <small>(id: {tenant.room.id}; owner: {tenant.room.owner.name})</small>
                  </td>
                  <td>{tenant.authUser && tenant.authUser.username || '(unknown)'}</td>
                  {isTestable &&
                    <td>
                      <a className="btn btn-default btn-sm"
                         onClick={this.onTest}>Test</a>
                    </td>
                  }
                </tr>
              );
            })}
          </tbody>
        </table>
        <p>
          To manage HipChat notifications or the rooms in which Sentry errors appear, visit the
          <a href={url} target="_blank"> integration configuration page</a>.
        </p>
        <p>
          <b>Disabling the plugin here will delete all associations
            and will disable notifications to all HipChat Rooms</b>
        </p>
      </div>
    );
  }

  render() {
    let metadata = this.props.plugin.metadata;

    let url = ('/plugins/hipchat-ac/start/' + this.props.organization.slug +
               '/' + this.props.project.slug)
    return (
      <div className="ref-hipchat-settings">
        {this.state.testResults &&
          <div className="ref-hipchat-test-results">
            <h4>Test Results</h4>
            {this.state.testResults.error ?
              <div className="alert alert-block alert-error">{this.state.testResults.message}</div>
            :
              <div className="alert alert-block alert-success">{this.state.testResults.message}</div>
            }
          </div>
        }
        {this.renderLink(url, metadata)}
        {this.renderTenants(url)}
      </div>
    );
  }
}

export default Settings;

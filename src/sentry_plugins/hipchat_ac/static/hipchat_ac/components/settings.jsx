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

  renderTenants() {
    if (this.state.tenantsLoading)
      return <LoadingIndicator />;
    else if (this.state.tenantsError)
      return <LoadingError onRetry={this.fetchData} />;

    let tenants = this.state.tenants;
    if (!tenants.length)
      return <p>The plugin is currently not active in any rooms.</p>;

    let isTestable = this.props.plugin.isTestable;
    return (
      <div>
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
          You can add or remove rooms directly from within Hipchat.  If you
          disable the plugin here, all associations are automatically deleted
          and this project will no longer notify in any rooms.
        </p>
      </div>
    );
  }

  render() {
    let metadata = this.props.plugin.metadata;

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

        <p>
          Hipchat notifications are managed through Hipchat itself.  After you
          added the Sentry integration directly into Hipchat you can add projects
          directly from there to your rooms.
        </p>
        <p>
          This page only shows in which rooms the project shows up.  To add or
          remove them, you need to use the integration configuration page.
        </p>
        <p>
          If you use the cloud hosted hipchat installation, you can one-click
          install the integration:
        </p>
        <p>
          <a href={metadata.installUrl}
             className="btn btn-primary"
             target="_blank">Enable Integration</a>
        </p>
        <p>
          Alternatively to add the Sentry integration to Hipchat click on "Install an
          integration from a descriptor URL" on your room in Hipchat and add the
          following descriptor URL:
        </p>
        <pre>{metadata.descriptor}</pre>
        <h4>Active Rooms</h4>
        {this.renderTenants()}
      </div>
    );
  }
}

export default Settings;

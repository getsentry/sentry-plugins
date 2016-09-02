(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.AP = f()}})(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(_dereq_,module,exports){
'use strict';

var _createClass = (function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ('value' in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; })();

var _get = function get(_x, _x2, _x3) { var _again = true; _function: while (_again) { var object = _x, property = _x2, receiver = _x3; desc = parent = getter = undefined; _again = false; if (object === null) object = Function.prototype; var desc = Object.getOwnPropertyDescriptor(object, property); if (desc === undefined) { var parent = Object.getPrototypeOf(object); if (parent === null) { return undefined; } else { _x = parent; _x2 = property; _x3 = receiver; _again = true; continue _function; } } else if ('value' in desc) { return desc.value; } else { var getter = desc.get; if (getter === undefined) { return undefined; } return getter.call(receiver); } } };

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { 'default': obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError('Cannot call a class as a function'); } }

function _inherits(subClass, superClass) { if (typeof superClass !== 'function' && superClass !== null) { throw new TypeError('Super expression must either be null or a function, not ' + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) subClass.__proto__ = superClass; }

var _commonUtil = _dereq_('../common/util');

var _commonUtil2 = _interopRequireDefault(_commonUtil);

var _commonPostmessage = _dereq_('../common/postmessage');

var _commonPostmessage2 = _interopRequireDefault(_commonPostmessage);

var AP = (function (_PostMessage) {
  function AP() {
    _classCallCheck(this, AP);

    _get(Object.getPrototypeOf(AP.prototype), 'constructor', this).call(this);
    this._data = this._parseInitData();
    this._host = window.parent;
    this._hostModules = {};
    this._eventHandlers = {};
    this._pendingCallbacks = {};
    this._setupAPI(this._data.api);
    this._messageHandlers = {
      resp: this._handleResponse,
      evt: this._handleEvent
    };

    window.addEventListener('DOMContentLoaded', _commonUtil2['default']._bind(this, this._sendInit));
  }

  _inherits(AP, _PostMessage);

  _createClass(AP, [{
    key: '_parseInitData',

    /**
    * The initialization data is passed in when the iframe is created as its 'name' attribute.
    * Example:
    * {
    *   extension_id: The ID of this iframe as defined by the host
    *   origin: 'https://example.org'  // The parent's window origin
    *   api: {
    *     _globals: { ... },
    *     messages = {
    *       clear: {},
    *       ...
    *     },
    *     ...
    *   }
    * }
    **/
    value: function _parseInitData(data) {
      try {
        return JSON.parse(data || window.name);
      } catch (e) {
        return {};
      }
    }
  }, {
    key: '_createModule',
    value: function _createModule(moduleName, api) {
      var _this = this;

      return Object.getOwnPropertyNames(api).reduce(function (accumulator, functionName) {
        accumulator[functionName] = _this._createMethodHandler({
          mod: moduleName,
          fn: functionName
        });
        return accumulator;
      }, {});
    }
  }, {
    key: '_setupAPI',
    value: function _setupAPI(api) {
      var _this2 = this;

      this._hostModules = Object.getOwnPropertyNames(api).reduce(function (accumulator, moduleName) {
        accumulator[moduleName] = _this2._createModule(moduleName, api[moduleName]);
        return accumulator;
      }, {});

      Object.getOwnPropertyNames(this._hostModules._globals || {}).forEach(function (global) {
        _this2[global] = _this2._hostModules._globals[global];
      });
    }
  }, {
    key: '_pendingCallback',
    value: function _pendingCallback(mid, fn) {
      this._pendingCallbacks[mid] = fn;
    }
  }, {
    key: '_createMethodHandler',
    value: function _createMethodHandler(methodData) {
      var methodHandler = function methodHandler() {
        var mid = undefined,
            args = _commonUtil2['default'].argumentsToArray(arguments);
        if (_commonUtil2['default'].hasCallback(args)) {
          mid = _commonUtil2['default'].randomString();
          this._pendingCallback(mid, args.pop());
        }
        this._host.postMessage({
          eid: this._data.extension_id,
          type: 'req',
          mid: mid,
          mod: methodData.mod,
          fn: methodData.fn,
          args: args
        }, this._data.origin);
      };

      return _commonUtil2['default']._bind(this, methodHandler);
    }
  }, {
    key: '_handleResponse',
    value: function _handleResponse(event) {
      var data = event.data;
      var pendingCallback = this._pendingCallbacks[data.mid];
      if (pendingCallback) {
        delete this._pendingCallbacks[data.mid];
        pendingCallback.apply(window, data.args);
      }
    }
  }, {
    key: '_handleEvent',
    value: function _handleEvent(event) {
      var sendResponse = function sendResponse() {
        var args = _commonUtil2['default'].argumentsToArray(arguments);
        event.source.postMessage({
          eid: this._data.extension_id,
          mid: event.data.mid,
          type: 'resp',
          args: args
        }, this._data.origin);
      };
      sendResponse = _commonUtil2['default']._bind(this, sendResponse);
      var data = event.data;
      var handler = this._eventHandlers[data.etyp];
      if (handler) {
        handler(data.evnt, sendResponse);
      } else if (data.mid) {
        sendResponse();
      }
    }
  }, {
    key: '_checkOrigin',
    value: function _checkOrigin(event) {
      return event.origin === this._data.origin && event.source === this._host;
    }
  }, {
    key: '_sendInit',
    value: function _sendInit() {
      this._host.postMessage({
        eid: this._data.extension_id,
        type: 'init'
      }, this._data.origin);
    }
  }, {
    key: 'require',
    value: function _dereq_(modules, callback) {
      var _this3 = this;

      var requiredModules = Array.isArray(modules) ? modules : [modules],
          args = requiredModules.map(function (module) {
        return _this3._hostModules[module];
      });
      callback.apply(window, args);
    }
  }, {
    key: 'register',
    value: function register(handlers) {
      this._eventHandlers = handlers || {};
      this._host.postMessage({
        eid: this._data.extension_id,
        type: 'event_query',
        args: Object.getOwnPropertyNames(handlers)
      }, this._data.origin);
    }
  }]);

  return AP;
})(_commonPostmessage2['default']);

module.exports = new AP();

},{"../common/postmessage":2,"../common/util":3}],2:[function(_dereq_,module,exports){
"use strict";

var _createClass = (function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; })();

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var _util = _dereq_("./util");

var _util2 = _interopRequireDefault(_util);

var PostMessage = (function () {
  function PostMessage(data) {
    _classCallCheck(this, PostMessage);

    var d = data || {};
    this._registerListener(d.listenOn);
  }

  _createClass(PostMessage, [{
    key: "_registerListener",

    // listen for postMessage events (defaults to window).
    value: function _registerListener(listenOn) {
      if (!listenOn || !listenOn.addEventListener) {
        listenOn = window;
      }
      listenOn.addEventListener("message", _util2["default"]._bind(this, this._receiveMessage), false);
    }
  }, {
    key: "_receiveMessage",
    value: function _receiveMessage(event) {
      var extensionId = event.data.eid,
          reg = undefined;

      if (extensionId && this._registeredExtensions) {
        reg = this._registeredExtensions[extensionId];
      }

      if (!this._checkOrigin(event, reg)) {
        return false;
      }

      var handler = this._messageHandlers[event.data.type];
      if (handler) {
        handler.call(this, event, reg);
      }
    }
  }]);

  return PostMessage;
})();

module.exports = PostMessage;

},{"./util":3}],3:[function(_dereq_,module,exports){
'use strict';

var _createClass = (function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ('value' in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; })();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError('Cannot call a class as a function'); } }

var Util = (function () {
  function Util() {
    _classCallCheck(this, Util);
  }

  _createClass(Util, [{
    key: 'randomString',
    value: function randomString() {
      return Math.floor(Math.random() * 1000000000).toString(16);
    }
  }, {
    key: 'argumentsToArray',

    // might be un-needed
    value: function argumentsToArray(arrayLike) {
      var array = [];
      for (var i = 0; i < arrayLike.length; i++) {
        array.push(arrayLike[i]);
      }
      return array;
    }
  }, {
    key: 'hasCallback',
    value: function hasCallback(args) {
      var length = args.length;
      return length > 0 && typeof args[length - 1] === 'function';
    }
  }, {
    key: '_bind',
    value: function _bind(thisp, fn) {
      if (Function.prototype.bind) {
        return fn.bind(thisp);
      }
      return function () {
        return fn.apply(thisp, arguments);
      };
    }
  }]);

  return Util;
})();

module.exports = new Util();

},{}]},{},[1])(1)
});
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyaWZ5L25vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCIvVXNlcnMvY3doaXR0aW5ndG9uL0RvY3VtZW50cy9zaW1wbGUteGRtL3NyYy9wbHVnaW4vaW5kZXguanMiLCIvVXNlcnMvY3doaXR0aW5ndG9uL0RvY3VtZW50cy9zaW1wbGUteGRtL3NyYy9jb21tb24vcG9zdG1lc3NhZ2UuanMiLCIvVXNlcnMvY3doaXR0aW5ndG9uL0RvY3VtZW50cy9zaW1wbGUteGRtL3NyYy9jb21tb24vdXRpbC5qcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTs7Ozs7Ozs7Ozs7OzswQkNBaUIsZ0JBQWdCOzs7O2lDQUNULHVCQUF1Qjs7OztJQUV6QyxFQUFFO0FBRUssV0FGUCxFQUFFLEdBRVE7MEJBRlYsRUFBRTs7QUFHSiwrQkFIRSxFQUFFLDZDQUdJO0FBQ1IsUUFBSSxDQUFDLEtBQUssR0FBRyxJQUFJLENBQUMsY0FBYyxFQUFFLENBQUM7QUFDbkMsUUFBSSxDQUFDLEtBQUssR0FBRyxNQUFNLENBQUMsTUFBTSxDQUFDO0FBQzNCLFFBQUksQ0FBQyxZQUFZLEdBQUcsRUFBRSxDQUFDO0FBQ3ZCLFFBQUksQ0FBQyxjQUFjLEdBQUcsRUFBRSxDQUFDO0FBQ3pCLFFBQUksQ0FBQyxpQkFBaUIsR0FBRyxFQUFFLENBQUM7QUFDNUIsUUFBSSxDQUFDLFNBQVMsQ0FBQyxJQUFJLENBQUMsS0FBSyxDQUFDLEdBQUcsQ0FBQyxDQUFDO0FBQy9CLFFBQUksQ0FBQyxnQkFBZ0IsR0FBRztBQUNwQixVQUFJLEVBQUUsSUFBSSxDQUFDLGVBQWU7QUFDMUIsU0FBRyxFQUFFLElBQUksQ0FBQyxZQUFZO0tBQ3pCLENBQUM7O0FBRUYsVUFBTSxDQUFDLGdCQUFnQixDQUFDLGtCQUFrQixFQUFFLHdCQUFLLEtBQUssQ0FBQyxJQUFJLEVBQUUsSUFBSSxDQUFDLFNBQVMsQ0FBQyxDQUFDLENBQUM7R0FDL0U7O1lBaEJHLEVB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LFVBQUksS0FBSyxHQUFHLEVBQUUsQ0FBQztBQUNmLFdBQUssSUFBSSxDQUFDLEdBQUcsQ0FBQyxFQUFFLENBQUMsR0FBRyxTQUFTLENBQUMsTUFBTSxFQUFFLENBQUMsRUFBRSxFQUFFO0FBQ3pDLGFBQUssQ0FBQyxJQUFJLENBQUMsU0FBUyxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7T0FDMUI7QUFDRCxhQUFPLEtBQUssQ0FBQztLQUNkOzs7V0FFVSxxQkFBQyxJQUFJLEVBQUU7QUFDaEIsVUFBSSxNQUFNLEdBQUcsSUFBSSxDQUFDLE1BQU0sQ0FBQztBQUN6QixhQUFPLE1BQU0sR0FBRyxDQUFDLElBQUksT0FBTyxJQUFJLENBQUMsTUFBTSxHQUFHLENBQUMsQ0FBQyxLQUFLLFVBQVUsQ0FBQztLQUM3RDs7O1dBRUksZUFBQyxLQUFLLEVBQUUsRUFBRSxFQUFDO0FBQ2QsVUFBRyxRQUFRLENBQUMsU0FBUyxDQUFDLElBQUksRUFBRTtBQUMxQixlQUFPLEVBQUUsQ0FBQyxJQUFJLENBQUMsS0FBSyxDQUFDLENBQUM7T0FDdkI7QUFDRCxhQUFPLFlBQVk7QUFDakIsZUFBTyxFQUFFLENBQUMsS0FBSyxDQUFDLEtBQUssRUFBRSxTQUFTLENBQUMsQ0FBQztPQUNuQyxDQUFDO0tBQ0g7OztTQXpCRyxJQUFJOzs7QUE2QlYsTUFBTSxDQUFDLE9BQU8sR0FBRyxJQUFJLElBQUksRUFBRSxDQUFDIiwiZmlsZSI6ImdlbmVyYXRlZC5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzQ29udGVudCI6WyIoZnVuY3Rpb24gZSh0LG4scil7ZnVuY3Rpb24gcyhvLHUpe2lmKCFuW29dKXtpZighdFtvXSl7dmFyIGE9dHlwZW9mIHJlcXVpcmU9PVwiZnVuY3Rpb25cIiYmcmVxdWlyZTtpZighdSYmYSlyZXR1cm4gYShvLCEwKTtpZihpKXJldHVybiBpKG8sITApO3ZhciBmPW5ldyBFcnJvcihcIkNhbm5vdCBmaW5kIG1vZHVsZSAnXCIrbytcIidcIik7dGhyb3cgZi5jb2RlPVwiTU9EVUxFX05PVF9GT1VORFwiLGZ9dmFyIGw9bltvXT17ZXhwb3J0czp7fX07dFtvXVswXS5jYWxsKGwuZXhwb3J0cyxmdW5jdGlvbihlKXt2YXIgbj10W29dWzFdW2VdO3JldHVybiBzKG4/bjplKX0sbCxsLmV4cG9ydHMsZSx0LG4scil9cmV0dXJuIG5bb10uZXhwb3J0c312YXIgaT10eXBlb2YgcmVxdWlyZT09XCJmdW5jdGlvblwiJiZyZXF1aXJlO2Zvcih2YXIgbz0wO288ci5sZW5ndGg7bysrKXMocltvXSk7cmV0dXJuIHN9KSIsImltcG9ydCBVdGlsIGZyb20gJy4uL2NvbW1vbi91dGlsJztcbmltcG9ydCBQb3N0TWVzc2FnZSBmcm9tICcuLi9jb21tb24vcG9zdG1lc3NhZ2UnO1xuXG5jbGFzcyBBUCBleHRlbmRzIFBvc3RNZXNzYWdlIHtcblxuICBjb25zdHJ1Y3RvcigpIHtcbiAgICBzdXBlcigpO1xuICAgIHRoaXMuX2RhdGEgPSB0aGlzLl9wYXJzZUluaXREYXRhKCk7XG4gICAgdGhpcy5faG9zdCA9IHdpbmRvdy5wYXJlbnQ7XG4gICAgdGhpcy5faG9zdE1vZHVsZXMgPSB7fTtcbiAgICB0aGlzLl9ldmVudEhhbmRsZXJzID0ge307XG4gICAgdGhpcy5fcGVuZGluZ0NhbGxiYWNrcyA9IHt9O1xuICAgIHRoaXMuX3NldHVwQVBJKHRoaXMuX2RhdGEuYXBpKTtcbiAgICB0aGlzLl9tZXNzYWdlSGFuZGxlcnMgPSB7XG4gICAgICAgIHJlc3A6IHRoaXMuX2hhbmRsZVJlc3BvbnNlLFxuICAgICAgICBldnQ6IHRoaXMuX2hhbmRsZUV2ZW50XG4gICAgfTtcblxuICAgIHdpbmRvdy5hZGRFdmVudExpc3RlbmVyKFwiRE9NQ29udGVudExvYWRlZFwiLCBVdGlsLl9iaW5kKHRoaXMsIHRoaXMuX3NlbmRJbml0KSk7XG4gIH1cbiAgLyoqXG4gICogVGhlIGluaXRpYWxpemF0aW9uIGRhdGEgaXMgcGFzc2VkIGluIHdoZW4gdGhlIGlmcmFtZSBpcyBjcmVhdGVkIGFzIGl0cyAnbmFtZScgYXR0cmlidXRlLlxuICAqIEV4YW1wbGU6XG4gICoge1xuICAqICAgZXh0ZW5zaW9uX2lkOiBUaGUgSUQgb2YgdGhpcyBpZnJhbWUgYXMgZGVmaW5lZCBieSB0aGUgaG9zdFxuICAqICAgb3JpZ2luOiAnaHR0cHM6Ly9leGFtcGxlLm9yZycgIC8vIFRoZSBwYXJlbnQncyB3aW5kb3cgb3JpZ2luXG4gICogICBhcGk6IHtcbiAgKiAgICAgX2dsb2JhbHM6IHsgLi4uIH0sXG4gICogICAgIG1lc3NhZ2VzID0ge1xuICAqICAgICAgIGNsZWFyOiB7fSxcbiAgKiAgICAgICAuLi5cbiAgKiAgICAgfSxcbiAgKiAgICAgLi4uXG4gICogICB9XG4gICogfVxuICAqKi9cbiAgX3BhcnNlSW5pdERhdGEoZGF0YSkge1xuICAgIHRyeSB7XG4gICAgICByZXR1cm4gSlNPTi5wYXJzZShkYXRhIHx8IHdpbmRvdy5uYW1lKTtcbiAgICB9IGNhdGNoIChlKSB7XG4gICAgICByZXR1cm4ge307XG4gICAgfVxuICB9XG5cbiAgX2NyZWF0ZU1vZHVsZShtb2R1bGVOYW1lLCBhcGkpIHtcbiAgICByZXR1cm4gT2JqZWN0LmdldE93blByb3BlcnR5TmFtZXMoYXBpKS5yZWR1Y2UoKGFjY3VtdWxhdG9yLCBmdW5jdGlvbk5hbWUpID0+IHtcbiAgICAgIGFjY3VtdWxhdG9yW2Z1bmN0aW9uTmFtZV0gPSB0aGlzLl9jcmVhdGVNZXRob2RIYW5kbGVyKHtcbiAgICAgICAgICBtb2Q6IG1vZHVsZU5hbWUsXG4gICAgICAgICAgZm46IGZ1bmN0aW9uTmFtZVxuICAgICAgfSk7XG4gICAgICByZXR1cm4gYWNjdW11bGF0b3I7XG4gICAgfSwge30pO1xuICB9XG5cbiAgX3NldHVwQVBJKGFwaSkge1xuICAgIHRoaXMuX2hvc3RNb2R1bGVzID0gT2JqZWN0LmdldE93blByb3BlcnR5TmFtZXMoYXBpKS5yZWR1Y2UoKGFjY3VtdWxhdG9yLCBtb2R1bGVOYW1lKSA9PiB7XG4gICAgICAgIGFjY3VtdWxhdG9yW21vZHVsZU5hbWVdID0gdGhpcy5fY3JlYXRlTW9kdWxlKG1vZHVsZU5hbWUsIGFwaVttb2R1bGVOYW1lXSk7XG4gICAgICAgIHJldHVybiBhY2N1bXVsYXRvcjtcbiAgICB9LCB7fSk7XG5cbiAgICBPYmplY3QuZ2V0T3duUHJvcGVydHlOYW1lcyh0aGlzLl9ob3N0TW9kdWxlcy5fZ2xvYmFscyB8fCB7fSkuZm9yRWFjaCgoZ2xvYmFsKSA9PiB7XG4gICAgICAgIHRoaXNbZ2xvYmFsXSA9IHRoaXMuX2hvc3RNb2R1bGVzLl9nbG9iYWxzW2dsb2JhbF07XG4gICAgfSk7XG4gIH1cblxuICBfcGVuZGluZ0NhbGxiYWNrKG1pZCwgZm4pe1xuICAgIHRoaXMuX3BlbmRpbmdDYWxsYmFja3NbbWlkXSA9IGZuO1xuICB9XG5cbiAgX2NyZWF0ZU1ldGhvZEhhbmRsZXIobWV0aG9kRGF0YSkge1xuICAgIGxldCBtZXRob2RIYW5kbGVyID0gZnVuY3Rpb24gKCkge1xuICAgICAgbGV0IG1pZCxcbiAgICAgICAgICBhcmdzID0gVXRpbC5hcmd1bWVudHNUb0FycmF5KGFyZ3VtZW50cyk7XG4gICAgICBpZiAoVXRpbC5oYXNDYWxsYmFjayhhcmdzKSkge1xuICAgICAgICBtaWQgPSBVdGlsLnJhbmRvbVN0cmluZygpO1xuICAgICAgICB0aGlzLl9wZW5kaW5nQ2FsbGJhY2sobWlkLCBhcmdzLnBvcCgpKTtcbiAgICAgIH1cbiAgICAgIHRoaXMuX2hvc3QucG9zdE1lc3NhZ2Uoe1xuICAgICAgICAgIGVpZDogdGhpcy5fZGF0YS5leHRlbnNpb25faWQsXG4gICAgICAgICAgdHlwZTogJ3JlcScsXG4gICAgICAgICAgbWlkOiBtaWQsXG4gICAgICAgICAgbW9kOiBtZXRob2REYXRhLm1vZCxcbiAgICAgICAgICBmbjogbWV0aG9kRGF0YS5mbixcbiAgICAgICAgICBhcmdzOiBhcmdzXG4gICAgICB9LCB0aGlzLl9kYXRhLm9yaWdpbik7XG4gICAgfTtcblxuICAgIHJldHVybiBVdGlsLl9iaW5kKHRoaXMsIG1ldGhvZEhhbmRsZXIpO1xuICB9XG5cbiAgX2hhbmRsZVJlc3BvbnNlKGV2ZW50KSB7XG4gICAgdmFyIGRhdGEgPSBldmVudC5kYXRhO1xuICAgIHZhciBwZW5kaW5nQ2FsbGJhY2sgPSB0aGlzLl9wZW5kaW5nQ2FsbGJhY2tzW2RhdGEubWlkXTtcbiAgICBpZiAocGVuZGluZ0NhbGxiYWNrKSB7XG4gICAgICBkZWxldGUgdGhpcy5fcGVuZGluZ0NhbGxiYWNrc1tkYXRhLm1pZF07XG4gICAgICBwZW5kaW5nQ2FsbGJhY2suYXBwbHkod2luZG93LCBkYXRhLmFyZ3MpO1xuICAgIH1cbiAgfVxuXG4gIF9oYW5kbGVFdmVudChldmVudCkge1xuICAgIHZhciBzZW5kUmVzcG9uc2UgPSBmdW5jdGlvbiAoKSB7XG4gICAgICB2YXIgYXJncyA9IFV0aWwuYXJndW1lbnRzVG9BcnJheShhcmd1bWVudHMpO1xuICAgICAgZXZlbnQuc291cmNlLnBvc3RNZXNzYWdlKHtcbiAgICAgICAgICBlaWQ6IHRoaXMuX2RhdGEuZXh0ZW5zaW9uX2lkLFxuICAgICAgICAgIG1pZDogZXZlbnQuZGF0YS5taWQsXG4gICAgICAgICAgdHlwZTogJ3Jlc3AnLFxuICAgICAgICAgIGFyZ3M6IGFyZ3NcbiAgICAgIH0sIHRoaXMuX2RhdGEub3JpZ2luKTtcbiAgICB9O1xuICAgIHNlbmRSZXNwb25zZSA9IFV0aWwuX2JpbmQodGhpcywgc2VuZFJlc3BvbnNlKTtcbiAgICB2YXIgZGF0YSA9IGV2ZW50LmRhdGE7XG4gICAgdmFyIGhhbmRsZXIgPSB0aGlzLl9ldmVudEhhbmRsZXJzW2RhdGEuZXR5cF07XG4gICAgaWYgKGhhbmRsZXIpIHtcbiAgICAgICAgaGFuZGxlcihkYXRhLmV2bnQsIHNlbmRSZXNwb25zZSk7XG4gICAgfSBlbHNlIGlmIChkYXRhLm1pZCkge1xuICAgICAgICBzZW5kUmVzcG9uc2UoKTtcbiAgICB9XG4gIH1cblxuICBfY2hlY2tPcmlnaW4oZXZlbnQpIHtcbiAgICAgIHJldHVybiBldmVudC5vcmlnaW4gPT09IHRoaXMuX2RhdGEub3JpZ2luICYmIGV2ZW50LnNvdXJjZSA9PT0gdGhpcy5faG9zdDtcbiAgfVxuXG4gIF9zZW5kSW5pdCgpIHtcbiAgICB0aGlzLl9ob3N0LnBvc3RNZXNzYWdlKHtcbiAgICAgICAgZWlkOiB0aGlzLl9kYXRhLmV4dGVuc2lvbl9pZCxcbiAgICAgICAgdHlwZTogJ2luaXQnXG4gICAgfSwgdGhpcy5fZGF0YS5vcmlnaW4pO1xuICB9XG5cbiAgcmVxdWlyZShtb2R1bGVzLCBjYWxsYmFjaykge1xuICAgIGxldCByZXF1aXJlZE1vZHVsZXMgPSBBcnJheS5pc0FycmF5KG1vZHVsZXMpID8gbW9kdWxlcyA6IFttb2R1bGVzXSxcbiAgICAgICAgYXJncyA9IHJlcXVpcmVkTW9kdWxlcy5tYXAoKG1vZHVsZSkgPT4ge1xuICAgICAgICAgIHJldHVybiB0aGlzLl9ob3N0TW9kdWxlc1ttb2R1bGVdO1xuICAgICAgICB9KTtcbiAgICBjYWxsYmFjay5hcHBseSh3aW5kb3csIGFyZ3MpO1xuICB9XG5cbiAgcmVnaXN0ZXIoaGFuZGxlcnMpIHtcbiAgICB0aGlzLl9ldmVudEhhbmRsZXJzID0gaGFuZGxlcnMgfHwge307XG4gICAgdGhpcy5faG9zdC5wb3N0TWVzc2FnZSh7XG4gICAgICBlaWQ6IHRoaXMuX2RhdGEuZXh0ZW5zaW9uX2lkLFxuICAgICAgdHlwZTogJ2V2ZW50X3F1ZXJ5JyxcbiAgICAgIGFyZ3M6IE9iamVjdC5nZXRPd25Qcm9wZXJ0eU5hbWVzKGhhbmRsZXJzKVxuICAgIH0sIHRoaXMuX2RhdGEub3JpZ2luKTtcbiAgfVxuXG59XG5cbm1vZHVsZS5leHBvcnRzID0gbmV3IEFQKCk7XG4iLCJpbXBvcnQgVXRpbCBmcm9tICcuL3V0aWwnO1xuY2xhc3MgUG9zdE1lc3NhZ2Uge1xuXG4gIGNvbnN0cnVjdG9yKGRhdGEpIHtcbiAgICBsZXQgZCA9IGRhdGEgfHwge307XG4gICAgdGhpcy5fcmVnaXN0ZXJMaXN0ZW5lcihkLmxpc3Rlbk9uKTtcbiAgfVxuXG4gLy8gbGlzdGVuIGZvciBwb3N0TWVzc2FnZSBldmVudHMgKGRlZmF1bHRzIHRvIHdpbmRvdykuXG4gIF9yZWdpc3Rlckxpc3RlbmVyKGxpc3Rlbk9uKSB7XG4gICAgaWYoIWxpc3Rlbk9uIHx8ICFsaXN0ZW5Pbi5hZGRFdmVudExpc3RlbmVyKSB7XG4gICAgICBsaXN0ZW5PbiA9IHdpbmRvdztcbiAgICB9XG4gICAgbGlzdGVuT24uYWRkRXZlbnRMaXN0ZW5lcihcIm1lc3NhZ2VcIiwgVXRpbC5fYmluZCh0aGlzLCB0aGlzLl9yZWNlaXZlTWVzc2FnZSksIGZhbHNlKTtcbiAgfVxuXG4gIF9yZWNlaXZlTWVzc2FnZSAoZXZlbnQpIHtcbiAgICBsZXQgZXh0ZW5zaW9uSWQgPSBldmVudC5kYXRhLmVpZCxcbiAgICByZWc7XG5cbiAgICBpZihleHRlbnNpb25JZCAmJiB0aGlzLl9yZWdpc3RlcmVkRXh0ZW5zaW9ucyl7XG4gICAgICByZWcgPSB0aGlzLl9yZWdpc3RlcmVkRXh0ZW5zaW9uc1tleHRlbnNpb25JZF07XG4gICAgfVxuXG4gICAgaWYgKCF0aGlzLl9jaGVja09yaWdpbihldmVudCwgcmVnKSkge1xuICAgICAgcmV0dXJuIGZhbHNlO1xuICAgIH1cblxuICAgIHZhciBoYW5kbGVyID0gdGhpcy5fbWVzc2FnZUhhbmRsZXJzW2V2ZW50LmRhdGEudHlwZV07XG4gICAgaWYgKGhhbmRsZXIpIHtcbiAgICAgIGhhbmRsZXIuY2FsbCh0aGlzLCBldmVudCwgcmVnKTtcbiAgICB9XG4gIH1cblxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IFBvc3RNZXNzYWdlOyIsImNsYXNzIFV0aWwge1xuICByYW5kb21TdHJpbmcoKSB7XG4gICAgcmV0dXJuIE1hdGguZmxvb3IoTWF0aC5yYW5kb20oKSAqIDEwMDAwMDAwMDApLnRvU3RyaW5nKDE2KTtcbiAgfVxuICAvLyBtaWdodCBiZSB1bi1uZWVkZWRcbiAgYXJndW1lbnRzVG9BcnJheShhcnJheUxpa2UpIHtcbiAgICB2YXIgYXJyYXkgPSBbXTtcbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IGFycmF5TGlrZS5sZW5ndGg7IGkrKykge1xuICAgICAgYXJyYXkucHVzaChhcnJheUxpa2VbaV0pO1xuICAgIH1cbiAgICByZXR1cm4gYXJyYXk7XG4gIH1cblxuICBoYXNDYWxsYmFjayhhcmdzKSB7XG4gICAgdmFyIGxlbmd0aCA9IGFyZ3MubGVuZ3RoO1xuICAgIHJldHVybiBsZW5ndGggPiAwICYmIHR5cGVvZiBhcmdzW2xlbmd0aCAtIDFdID09PSAnZnVuY3Rpb24nO1xuICB9XG5cbiAgX2JpbmQodGhpc3AsIGZuKXtcbiAgICBpZihGdW5jdGlvbi5wcm90b3R5cGUuYmluZCkge1xuICAgICAgcmV0dXJuIGZuLmJpbmQodGhpc3ApO1xuICAgIH1cbiAgICByZXR1cm4gZnVuY3Rpb24gKCkge1xuICAgICAgcmV0dXJuIGZuLmFwcGx5KHRoaXNwLCBhcmd1bWVudHMpO1xuICAgIH07XG4gIH1cblxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IG5ldyBVdGlsKCk7Il19

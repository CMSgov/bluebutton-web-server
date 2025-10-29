function _extends() { _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; }; return _extends.apply(this, arguments); }

import React from 'react';
import classNames from 'classnames';
import uniqueId from 'lodash/uniqueId';
import { SvgIcon } from '@cmsgov/design-system';
var defaultProps = {
  className: '',
  title: 'Half Star'
};

var RoundedStarHalfIcon = function RoundedStarHalfIcon(props) {
  var clipPath1 = uniqueId('clip_path_');
  var clipPath2 = uniqueId('clip_path_');
  var clipPath3 = uniqueId('clip_path_');
  var filterId = uniqueId('star_filter_');
  var maskId = uniqueId('star_mask_');
  var iconCssClasses = classNames('ds-c-icon--rounded-star', 'ds-c-icon--rounded-star-half', props.className);
  return /*#__PURE__*/React.createElement(SvgIcon, _extends({}, defaultProps, props, {
    className: iconCssClasses
  }), /*#__PURE__*/React.createElement("g", null, /*#__PURE__*/React.createElement("g", null, /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath1
  }, /*#__PURE__*/React.createElement("path", {
    d: "M11.5,3.6L9.3,8.3L4.4,9c-0.9,0.1-1.2,1.3-0.6,1.9l3.6,3.6l-0.8,5.1c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4 l4.4,2.4c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7l-2.2-4.7C13.1,2.8,11.9,2.8,11.5,3.6z"
  })), /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath2
  }, /*#__PURE__*/React.createElement("rect", {
    x: "-7.5",
    y: "-8",
    width: "40",
    height: "40"
  })), /*#__PURE__*/React.createElement("clipPath", {
    id: clipPath3
  }, /*#__PURE__*/React.createElement("rect", {
    x: "3.5",
    y: "3",
    width: "18",
    height: "18"
  })), /*#__PURE__*/React.createElement("g", {
    clipPath: "url(#".concat(clipPath1, ")")
  }, /*#__PURE__*/React.createElement("g", {
    clipPath: "url(#".concat(clipPath2, ")"),
    fill: "none",
    stroke: "#1E3C70",
    strokeWidth: 2,
    strokeMiterlimit: 10
  }, /*#__PURE__*/React.createElement("path", {
    clipPath: "url(#".concat(clipPath3, ")"),
    d: "M11.5,3.6L9.3,8.3L4.4,9c-0.9,0.1-1.2,1.3-0.6,1.9l3.6,3.6l-0.8,5.1c-0.2,0.9,0.8,1.6,1.6,1.2l4.4-2.4 l4.4,2.4c0.8,0.4,1.7-0.3,1.6-1.2l-0.8-5.1l3.6-3.6c0.6-0.7,0.3-1.8-0.6-1.9l-4.9-0.7l-2.2-4.7C13.1,2.8,11.9,2.8,11.5,3.6z"
  })))), /*#__PURE__*/React.createElement("filter", {
    id: filterId,
    filterUnits: "userSpaceOnUse",
    x: "3",
    y: "3",
    width: "19",
    height: "18"
  }, /*#__PURE__*/React.createElement("feColorMatrix", {
    type: "matrix",
    values: "1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0"
  })), /*#__PURE__*/React.createElement("mask", {
    maskUnits: "userSpaceOnUse",
    x: "3",
    y: "3",
    width: "19",
    height: "18",
    id: maskId
  }, /*#__PURE__*/React.createElement("g", {
    filter: "url(#".concat(filterId, ")")
  }, /*#__PURE__*/React.createElement("rect", {
    x: "2",
    y: "1",
    width: "10.5",
    height: "21",
    fill: "#FFFFFF",
    fillRule: "evenodd",
    clipRule: "evenodd"
  }))), /*#__PURE__*/React.createElement("path", {
    className: "HalfStarPath",
    fill: "currentColor",
    fillRule: "evenodd",
    clipRule: "evenodd",
    mask: "url(#".concat(maskId, ")"),
    d: "M11.5,3.6L9.2,8.3L4,9C3,9.2,2.7,10.3,3.3,10.9l3.8,3.6l-0.9,5.1c-0.2,0.9,0.8,1.6,1.6,1.2 l4.6-2.4 l4.6,2.4c0.8,0.4,1.8-0.3,1.6-1.2l-0.9-5.1l3.8-3.6C22.3,10.3,22,9.2,21,9l-5.2-0.7l-2.3-4.7C13.1,2.8,11.9,2.8,11.5,3.6z"
  })));
};

export default RoundedStarHalfIcon;
import React from 'react';
import { CheckIcon } from '@cmsgov/design-system';

var Checkmark = function Checkmark(_ref) {
  var className = _ref.className;
  console.error("[Deprecated]: Please use the <CheckIcon /> component with 'ds-c-icon-color--primary' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/React.createElement(CheckIcon, {
    className: "ds-c-icon-color--primary ".concat(className)
  });
};

export default Checkmark;
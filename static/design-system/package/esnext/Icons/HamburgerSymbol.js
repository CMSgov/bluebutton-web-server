import React from 'react';
import { MenuIconThin } from '@cmsgov/design-system';

var HamburgerSymbol = function HamburgerSymbol(_ref) {
  var className = _ref.className;
  console.error("[Deprecated]: Please use the <MenuIconThin /> component with 'ds-c-icon-color--primary' CSS class instead. This component will be removed in a future release.");
  return /*#__PURE__*/React.createElement(MenuIconThin, {
    className: "ds-c-icon-color--primary ".concat(className)
  });
};

export default HamburgerSymbol;
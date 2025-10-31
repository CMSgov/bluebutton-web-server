import React from 'react';
import { useEffect, useRef } from 'react';
import { HHSLogo, Button } from '@cmsgov/design-system';
import MedicaregovLogo from '../MedicaregovLogo/MedicaregovLogo';

var SimpleFooter = function SimpleFooter(_ref) {
  var _ref$aboutMedicareLab = _ref.aboutMedicareLabel,
      aboutMedicareLabel = _ref$aboutMedicareLab === void 0 ? 'About Medicare' : _ref$aboutMedicareLab,
      _ref$medicareGlossary = _ref.medicareGlossaryLabel,
      medicareGlossaryLabel = _ref$medicareGlossary === void 0 ? 'Medicare Glossary' : _ref$medicareGlossary,
      _ref$nondiscriminatio = _ref.nondiscriminationLabel,
      nondiscriminationLabel = _ref$nondiscriminatio === void 0 ? 'Nondiscrimination / Accessibility' : _ref$nondiscriminatio,
      _ref$privacyPolicyLab = _ref.privacyPolicyLabel,
      privacyPolicyLabel = _ref$privacyPolicyLab === void 0 ? 'Privacy Policy' : _ref$privacyPolicyLab,
      _ref$privacySettingLa = _ref.privacySettingLabel,
      privacySettingLabel = _ref$privacySettingLa === void 0 ? 'Privacy Setting' : _ref$privacySettingLa,
      _ref$linkingPolicyLab = _ref.linkingPolicyLabel,
      linkingPolicyLabel = _ref$linkingPolicyLab === void 0 ? 'Linking Policy' : _ref$linkingPolicyLab,
      _ref$usingThisSiteLab = _ref.usingThisSiteLabel,
      usingThisSiteLabel = _ref$usingThisSiteLab === void 0 ? 'Using this site' : _ref$usingThisSiteLab,
      _ref$plainWritingLabe = _ref.plainWritingLabel,
      plainWritingLabel = _ref$plainWritingLabe === void 0 ? 'Plain Writing' : _ref$plainWritingLabe,
      _ref$language = _ref.language,
      language = _ref$language === void 0 ? 'en' : _ref$language,
      _ref$websiteInfo = _ref.websiteInfo,
      websiteInfo = _ref$websiteInfo === void 0 ? 'A federal government website managed and paid for by the U.S. Centers for Medicare and Medicaid Services.' : _ref$websiteInfo,
      onClickLinkAnalytics = _ref.onClickLinkAnalytics;
  var footerRef = useRef();
  useEffect(function () {
    if (onClickLinkAnalytics) {
      var _footerRef$current;

      (_footerRef$current = footerRef.current) === null || _footerRef$current === void 0 ? void 0 : _footerRef$current.querySelectorAll('a').forEach(function (anchor) {
        anchor.onclick = function () {
          return onClickLinkAnalytics(anchor.href);
        };
      });
    }
  }, [onClickLinkAnalytics]);
  return /*#__PURE__*/React.createElement("footer", {
    className: "m-c-footer",
    ref: footerRef
  }, /*#__PURE__*/React.createElement("div", {
    className: "m-c-footer__linkRow"
  }, /*#__PURE__*/React.createElement("div", {
    className: "m-c-footer__links"
  }, /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/about-us"
  }, aboutMedicareLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/glossary/a"
  }, medicareGlossaryLabel)), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/about-us/accessibility-nondiscrimination-notice"
  }, nondiscriminationLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/privacy-policy"
  }, privacyPolicyLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement(Button, {
    className: "SimpleFooter__linkButton",
    variation: "ghost",
    onClick: function onClick() {
      var utag = window.utag;

      if (utag && utag.gdpr && utag.gdpr.showConsentPreferences(language) && typeof window.utag.gdpr.showConsentPreferences === 'function') {
        utag.gdpr.showConsentPreferences();
      }

      if (onClickLinkAnalytics) {
        onClickLinkAnalytics(privacySettingLabel);
      }
    }
  }, privacySettingLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement("a", {
    href: "https://www.cms.gov/About-CMS/Agency-Information/Aboutwebsite/index.html"
  }, linkingPolicyLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/about-us/using-this-site"
  }, usingThisSiteLabel), /*#__PURE__*/React.createElement("span", {
    "aria-hidden": "true",
    className: "m-c-footer__delimiter"
  }), /*#__PURE__*/React.createElement("a", {
    href: "https://www.medicare.gov/about-us/plain-writing"
  }, plainWritingLabel))), /*#__PURE__*/React.createElement("div", {
    className: "m-c-footer__identityRow"
  }, /*#__PURE__*/React.createElement(MedicaregovLogo, null), /*#__PURE__*/React.createElement("div", {
    className: "m-c-footer__identityContent"
  }, /*#__PURE__*/React.createElement(HHSLogo, null), /*#__PURE__*/React.createElement("span", {
    className: "m-c-footer__contactAddress"
  }, websiteInfo, /*#__PURE__*/React.createElement("br", null), "7500 Security Boulevard, Baltimore, MD 21244"))));
};

export default SimpleFooter;
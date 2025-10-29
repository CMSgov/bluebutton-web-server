import { FunctionComponent } from 'react';
interface SimpleFooterProps {
    aboutMedicareLabel?: string;
    medicareGlossaryLabel?: string;
    nondiscriminationLabel?: string;
    privacyPolicyLabel?: string;
    privacySettingLabel?: string;
    linkingPolicyLabel?: string;
    usingThisSiteLabel?: string;
    plainWritingLabel?: string;
    websiteInfo?: string;
    onClickLinkAnalytics?: (url: string) => void;
    /** Adds a proptype for changing language for the 'Privacy Setting' modal. See tealium documentation about 'Consent Preferences Manager', for more info. */
    language?: string;
}
declare const SimpleFooter: FunctionComponent<SimpleFooterProps>;
export default SimpleFooter;

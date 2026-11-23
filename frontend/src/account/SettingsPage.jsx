import Page from "../components/Page";
import useCurrentUser from "../hooks/useCurrentUser";
import ChangePasswordForm from "./ChangePasswordForm";
import DeleteAccountSection from "./DeleteAccountSection";

/** הגדרות: מה אפשר לשנות או לעשות בחשבון. */
export default function SettingsPage() {
  const { user } = useCurrentUser();

  return (
    <Page title="הגדרות" subtitle="סיסמה ואבטחת החשבון">
      {user ? (
        <>
          <ChangePasswordForm />
          <DeleteAccountSection />
        </>
      ) : (
        <p className="hint">טוען...</p>
      )}
    </Page>
  );
}

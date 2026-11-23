#include <QApplication>
#include <QFont>
#include <QStyle>
#include <QTimer>
#include <QPalette>
#include <QIcon>
#include <KIconTheme>
#include <cstdio>

static void add_probe() {
    QTimer::singleShot(1200, [] {
        auto app = qobject_cast<QApplication *>(QCoreApplication::instance());
        if (!app) return;
        const auto pal = app->palette();
        fprintf(stderr, "CARBON_WRAPPER platformtheme=%s GTK_THEME=%s\n",
                qgetenv("QT_QPA_PLATFORMTHEME").constData(), qgetenv("GTK_THEME").constData());
        fprintf(stderr, "CARBON_QT qpa=%s style=%s class=%s font=%s pt=%.1f icon=%s iconTheme=%s window=%s base=%s text=%s inactiveText=%s selection=%s selectedText=%s\n",
                qPrintable(app->platformName()), qPrintable(app->style()->objectName()), app->style()->metaObject()->className(),
                qPrintable(app->font().family()), app->font().pointSizeF(), qPrintable(QIcon::themeName()), qPrintable(KIconTheme::current()),
                qPrintable(pal.color(QPalette::Window).name()), qPrintable(pal.color(QPalette::Base).name()),
                qPrintable(pal.color(QPalette::Text).name()), qPrintable(pal.color(QPalette::Inactive,QPalette::Text).name()),
                qPrintable(pal.color(QPalette::Highlight).name()), qPrintable(pal.color(QPalette::HighlightedText).name()));
    });
}
Q_COREAPP_STARTUP_FUNCTION(add_probe)
